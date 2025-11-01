# chatbot_retriever.py
"""
Hybrid retriever:
 - loads PDFs & PPTX (robust imports)
 - chunks via RecursiveCharacterTextSplitter
 - BM25 (rank_bm25) + FAISS (IVF when possible) using SentenceTransformers
 - returns a combined context string limited by MAX_CONTEXT_CHARS
"""

import os
import re
import pickle
import logging
import shutil
import random
from typing import List, Optional, Dict, Any

import numpy as np
import faiss

from rank_bm25 import BM25Okapi
from langchain_community.document_loaders import UnstructuredFileLoader


# Document loaders: try langchain first, then community loader
try:
    from langchain.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
except Exception:
    # fallback to community package (older installations)
    try:
        from langchain_community.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
        from langchain_community.document_loaders.powerpoint import UnstructuredPowerPointLoader
    except Exception:
        raise ImportError("Please install langchain + langchain-community (or upgrade).")

from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# ---------- Config ----------
DATA_DIR = os.getenv("DATA_DIR", "data")
CACHE_DIR = os.getenv("CACHE_DIR", ".ragg_cache")
CHUNKS_CACHE = os.path.join(CACHE_DIR, "chunks.pkl")
BM25_CACHE = os.path.join(CACHE_DIR, "bm25.pkl")

FAISS_DIR = os.getenv("FAISS_DIR", "faiss_index")
FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "index.faiss")
FAISS_META_PATH = os.path.join(FAISS_DIR, "meta.pkl")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 400))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 80))
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

TOP_K_DOCS = int(os.getenv("TOP_K_DOCS", 3))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", 4000))

# FAISS params
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 256))
FAISS_NLIST = int(os.getenv("FAISS_NLIST", 100))
FAISS_TRAIN_SIZE = int(os.getenv("FAISS_TRAIN_SIZE", 2000))
FAISS_NPROBE = int(os.getenv("FAISS_NPROBE", 10))
SEARCH_EXPANSION = int(os.getenv("FAISS_SEARCH_EXPANSION", 5))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def detect_subject(fname: str) -> Optional[str]:
    # light heuristic to guess subject code from filename
    t = (fname or "").lower()
    if "network" in t or "cn" in t:
        return "cn"
    if "distributed" in t or "dos" in t:
        return "dos"
    if "software" in t or "se" in t:
        return "se"
    return None


def extract_year(s: str) -> Optional[str]:
    m = re.search(r"\b(20\d{2})\b", s)
    return m.group(1) if m else None


# ---------- Embeddings wrapper (SentenceTransformers) ----------
class Embeddings:
    def __init__(self, model_name=EMBED_MODEL):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vecs = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [v.astype("float32") for v in vecs]

    def embed_query(self, text: str) -> List[float]:
        v = self.model.encode([text], show_progress_bar=False, convert_to_numpy=True)[0]
        return v.astype("float32")


# ---------- Load documents ----------
def load_all_docs(base_dir: str = DATA_DIR) -> List:
    docs = []
    if not os.path.isdir(base_dir):
        logger.warning("Data dir does not exist: %s", base_dir)
        return docs

    def load_file(path: str, filename: str, category: str):
        try:
            fname = filename.lower()
            if fname.endswith(".pdf"):
                loader = PyPDFLoader(path)
            elif fname.endswith(".pptx"):
                loader = UnstructuredPowerPointLoader(path)
            else:
                return []
            file_docs = loader.load()
            subject = detect_subject(fname)
            year = extract_year(fname)
            for d in file_docs:
                d.metadata["subject"] = subject
                d.metadata["filename"] = filename
                d.metadata["category"] = category
                if year:
                    d.metadata["year"] = year
            return file_docs
        except Exception:
            logger.exception("Failed to load %s", filename)
            return []

    # root files
    for file in os.listdir(base_dir):
        path = os.path.join(base_dir, file)
        if os.path.isfile(path) and (file.lower().endswith(".pdf") or file.lower().endswith(".pptx")):
            docs.extend(load_file(path, file, "syllabus"))

    # optional pyqs directory
    pyqs_dir = os.path.join(base_dir, "pyqs")
    if os.path.isdir(pyqs_dir):
        for file in os.listdir(pyqs_dir):
            path = os.path.join(pyqs_dir, file)
            if os.path.isfile(path) and file.lower().endswith(".pdf"):
                docs.extend(load_file(path, file, "pyq"))

    logger.info("Loaded %d raw document pages", len(docs))
    return docs


# ---------- Build / load FAISS + BM25 ----------
def build_or_load_indexes(force_reindex: bool = False):
    if os.getenv("FORCE_REINDEX", "0").lower() in ("1", "true", "yes"):
        force_reindex = True

    docs = load_all_docs(DATA_DIR)
    if not docs:
        logger.warning("No documents found. Returning empty indexes.")
        return [], None, [], [], None

    # chunking
    if os.path.exists(CHUNKS_CACHE) and not force_reindex:
        with open(CHUNKS_CACHE, "rb") as f:
            chunks = pickle.load(f)
        logger.info("Loaded %d chunks from cache.", len(chunks))
    else:
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = splitter.split_documents(docs)
        with open(CHUNKS_CACHE, "wb") as f:
            pickle.dump(chunks, f)
        logger.info("Created and cached %d chunks.", len(chunks))

    corpus_texts = [c.page_content for c in chunks]

    # BM25
    if os.path.exists(BM25_CACHE) and not force_reindex:
        try:
            with open(BM25_CACHE, "rb") as f:
                bm25_data = pickle.load(f)
            bm25 = bm25_data.get("bm25")
            tokenized = bm25_data.get("tokenized", [])
            logger.info("Loaded BM25 from cache (n=%d)", len(corpus_texts))
        except Exception:
            logger.exception("Failed to load BM25 cache — rebuilding")
            tokenized = [re.findall(r"\w+", t.lower()) for t in corpus_texts]
            bm25 = BM25Okapi(tokenized)
            with open(BM25_CACHE, "wb") as f:
                pickle.dump({"bm25": bm25, "tokenized": tokenized}, f)
    else:
        tokenized = [re.findall(r"\w+", t.lower()) for t in corpus_texts]
        bm25 = BM25Okapi(tokenized)
        try:
            with open(BM25_CACHE, "wb") as f:
                pickle.dump({"bm25": bm25, "tokenized": tokenized}, f)
        except Exception:
            logger.warning("Could not write BM25 cache")

    # Embeddings
    embeddings = Embeddings()

    metadatas = [c.metadata for c in chunks]

    # load existing faiss index
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_META_PATH) and not force_reindex:
        try:
            index = faiss.read_index(FAISS_INDEX_PATH)
            with open(FAISS_META_PATH, "rb") as f:
                meta = pickle.load(f)
            texts = meta.get("texts", corpus_texts)
            try:
                index.nprobe = FAISS_NPROBE
            except Exception:
                pass
            logger.info("Loaded FAISS index from disk (%s), entries=%d", FAISS_INDEX_PATH, len(texts))
            return chunks, bm25, tokenized, corpus_texts, {"index": index, "texts": texts, "metadatas": metadatas, "embeddings": embeddings}
        except Exception:
            logger.exception("Failed to load FAISS index; rebuilding")

    # force reindex cleanup
    if force_reindex:
        try:
            shutil.rmtree(FAISS_DIR, ignore_errors=True)
            os.makedirs(FAISS_DIR, exist_ok=True)
        except Exception:
            pass

    # Build FAISS (memory-aware, batch)
    logger.info("Building FAISS index (nlist=%d). This may take a while...", FAISS_NLIST)
    total = len(corpus_texts)
    sample_size = min(total, FAISS_TRAIN_SIZE)
    sample_indices = random.sample(range(total), sample_size) if sample_size < total else list(range(total))

    sample_embs = []
    for i in range(0, len(sample_indices), BATCH_SIZE):
        batch_idx = sample_indices[i:i + BATCH_SIZE]
        batch_texts = [corpus_texts[j] for j in batch_idx]
        try:
            batch_vecs = embeddings.embed_documents(batch_texts)
        except Exception:
            batch_vecs = [embeddings.embed_query(t) for t in batch_texts]
        sample_embs.extend(batch_vecs)

    sample_np = np.array(sample_embs, dtype="float32")
    if sample_np.ndim == 1:
        sample_np = sample_np.reshape(1, -1)
    d = sample_np.shape[1]
    n_train_samples = sample_np.shape[0]

    use_ivf = True
    if n_train_samples < FAISS_NLIST:
        logger.warning("Not enough training samples (%d) for FAISS_NLIST=%d — using Flat index", n_train_samples, FAISS_NLIST)
        use_ivf = False

    try:
        if use_ivf:
            index_desc = f"IVF{FAISS_NLIST},Flat"
            index = faiss.index_factory(d, index_desc, faiss.METRIC_L2)
            if not index.is_trained:
                try:
                    index.train(sample_np)
                    logger.info("Trained IVF on %d samples", n_train_samples)
                except Exception:
                    logger.exception("IVF training failed — falling back to Flat")
                    index = faiss.index_factory(d, "Flat", faiss.METRIC_L2)
        else:
            index = faiss.index_factory(d, "Flat", faiss.METRIC_L2)
    except Exception:
        logger.exception("Failed to create FAISS index — using Flat")
        index = faiss.index_factory(d, "Flat", faiss.METRIC_L2)

    # add vectors in batches
    added = 0
    for i in range(0, total, BATCH_SIZE):
        batch_texts = corpus_texts[i:i + BATCH_SIZE]
        try:
            batch_vecs = embeddings.embed_documents(batch_texts)
        except Exception:
            batch_vecs = [embeddings.embed_query(t) for t in batch_texts]
        batch_np = np.array(batch_vecs, dtype="float32")
        if batch_np.ndim == 1:
            batch_np = batch_np.reshape(1, -1)
        index.add(batch_np)
        added += batch_np.shape[0]
        logger.info("FAISS: added %d / %d vectors", added, total)

    try:
        index.nprobe = FAISS_NPROBE
    except Exception:
        pass

    try:
        faiss.write_index(index, FAISS_INDEX_PATH)
        with open(FAISS_META_PATH, "wb") as f:
            pickle.dump({"texts": corpus_texts}, f)
        logger.info("FAISS index saved to %s (entries=%d)", FAISS_INDEX_PATH, total)
    except Exception:
        logger.exception("Failed to persist FAISS index on disk")

    return chunks, bm25, tokenized, corpus_texts, {"index": index, "texts": corpus_texts, "metadatas": metadatas, "embeddings": embeddings}


# ---------- Hybrid retrieve ----------
def _ensure_index_built():
    if not hasattr(hybrid_retrieve, "_index_built") or not hybrid_retrieve._index_built:
        hybrid_retrieve._chunks, hybrid_retrieve._bm25, hybrid_retrieve._tokenized, hybrid_retrieve._corpus, hybrid_retrieve._faiss = build_or_load_indexes()
        hybrid_retrieve._index_built = True


def _faiss_search(query: str, top_k: int = TOP_K_DOCS, subject: Optional[str] = None):
    faiss_data = hybrid_retrieve._faiss
    if not faiss_data:
        return []

    index = faiss_data.get("index")
    texts = faiss_data.get("texts", [])
    metadatas = faiss_data.get("metadatas", [{}] * len(texts))
    embeddings = faiss_data.get("embeddings")

    try:
        q_vec = embeddings.embed_query(query)
    except Exception:
        q_vec = embeddings.embed_documents([query])[0]

    q_np = np.array(q_vec, dtype="float32").reshape(1, -1)
    search_k = max(top_k * SEARCH_EXPANSION, top_k)
    try:
        distances, indices = index.search(q_np, int(search_k))
    except Exception:
        distances, indices = index.search(q_np, int(top_k))

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(texts):
            continue
        meta = metadatas[idx]
        if subject and meta.get("subject") != subject:
            continue
        score_like = float(-dist)
        results.append((score_like, meta, texts[idx]))
        if len(results) >= top_k:
            break

    return results


def hybrid_retrieve(query: str, subject: Optional[str] = None, top_k: int = TOP_K_DOCS, max_chars: int = MAX_CONTEXT_CHARS) -> Dict[str, Any]:
    if not query:
        return {"context": None, "bm25_docs": [], "faiss_docs": [], "meta": []}

    _ensure_index_built()

    chunks = hybrid_retrieve._chunks
    bm25 = hybrid_retrieve._bm25

    # BM25
    results_bm25 = []
    try:
        if bm25:
            q_tokens = re.findall(r"\w+", query.lower())
            scores = bm25.get_scores(q_tokens)
            ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            for i in ranked_idx:
                results_bm25.append((float(scores[i]), chunks[i].metadata, chunks[i].page_content))
    except Exception:
        logger.exception("BM25 search failed")

    # FAISS
    results_faiss = []
    try:
        results_faiss = _faiss_search(query, top_k=top_k, subject=subject)
    except Exception:
        logger.exception("FAISS search failed")

    # Merge and dedupe by text
    merged_texts = []
    merged_meta = []
    for score, meta, text in results_bm25:
        if text and text.strip() and text not in merged_texts:
            merged_texts.append(text)
            merged_meta.append({"source": meta.get("filename"), "subject": meta.get("subject"), "score": score})
    for score, meta, text in results_faiss:
        if text and text.strip() and text not in merged_texts:
            merged_texts.append(text)
            merged_meta.append({"source": meta.get("filename") if isinstance(meta, dict) else None, "subject": meta.get("subject") if isinstance(meta, dict) else None, "score": score})

    # compose context parts with headers
    context_parts = []
    for i, t in enumerate(merged_texts):
        header = f"\n\n===== DOC {i+1} =====\n"
        context_parts.append(header + t)
    context = "\n".join(context_parts).strip()
    if not context:
        return {"context": None, "bm25_docs": results_bm25, "faiss_docs": results_faiss, "meta": merged_meta}

    if len(context) > max_chars:
        context = context[:max_chars].rstrip() + "..."

    return {"context": context, "bm25_docs": results_bm25, "faiss_docs": results_faiss, "meta": merged_meta}


# ---------- retrieve_node (for reuse) ----------
def _last_n_user_messages(rows: List[tuple], n: int = 3) -> List[str]:
    """Return only the latest user message for retrieval context."""
    users = [r[1] for r in rows if r[0] == "user"]
    return users[-n:]  # only keep the last one

def retrieve_node_from_rows(rows: List[tuple], top_k: int = TOP_K_DOCS) -> Dict[str, Any]:
    last_users = _last_n_user_messages(rows, n=3)
    current_query = " ".join(last_users).strip() if last_users else ""
    if not current_query:
        return {"context": None, "direct": False}
    detected = None
    try:
        detected = detect_subject(current_query)
    except Exception:
        detected = None
    result = hybrid_retrieve(current_query, subject=detected, top_k=top_k, max_chars=MAX_CONTEXT_CHARS)
    return {"context": result.get("context"), "direct": False}
