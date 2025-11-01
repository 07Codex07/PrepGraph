# main_api.py
import os
import logging
import traceback
from typing import Optional, List, Dict, Any
import tiktoken

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# import your existing modules (assumed in same directory)
from memory_store import init_db, save_message, get_last_messages, clear_user_memory, build_gradio_history  # :contentReference[oaicite:4]{index=4}
from chatbot_retriever import build_or_load_indexes, hybrid_retrieve, retrieve_node_from_rows, load_all_docs  # :contentReference[oaicite:5]{index=5}
from chatbot_graph import SYSTEM_PROMPT, call_llm, _extract_answer_from_response  # :contentReference[oaicite:6]{index=6}

# ----------------- CORS SETUP -----------------
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RAG Chat Backend", version="1.0")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # ✅ lowercase 'allow_'
    allow_headers=["*"],   # ✅ lowercase 'allow_'
)
# ------------------------------------------------

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("rag_api")
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

# initialize DB now
init_db()

# Global in-memory flag/object to check indexes loaded (populated by build_or_load_indexes)
INDEXES = {"built": False, "info": None}


# ---------- Pydantic models ----------
class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    user_id: str
    message: str
    assistant: str
    history: List[Dict[str, str]]


class RetrieveResponse(BaseModel):
    query: str
    context: Optional[str]
    meta: List[Dict[str, Any]]


# ---------- helpers ----------
def ensure_indexes(force_reindex: bool = False):
    """
    Build or load indexes synchronously. This wraps build_or_load_indexes from chatbot_retriever.
    """
    if INDEXES["built"] and not force_reindex:
        return INDEXES["info"]
    try:
        chunks, bm25, tokenized, corpus_texts, faiss_data = build_or_load_indexes(force_reindex=force_reindex)
        INDEXES["built"] = True
        INDEXES["info"] = {"chunks_len": len(chunks) if chunks else 0, "corpus_len": len(corpus_texts) if corpus_texts else 0}
        return INDEXES["info"]
    except Exception:
        logger.exception("Index build/load failed")
        raise

# ===== Token limiter helper =====
enc = tiktoken.get_encoding("cl100k_base")

def trim_to_token_limit(texts, limit=4000):
    """Join text chunks until token limit is reached."""
    joined = ""
    for t in texts:
        if len(enc.encode(joined + t)) > limit:
            break
        joined += t + "\n"
    return joined

def extract_history_for_frontend(user_id: str, limit: int = 500):
    return build_gradio_history(user_id)


# ---------- Routes ----------
@app.get("/health")
def health():
    """Basic health check."""
    return {"status": "ok", "indexes_built": INDEXES["built"]}


@app.post("/reindex")
def reindex(force: Optional[bool] = False):
    """
    Force rebuild of indexes. This calls the same build_or_load_indexes used by your retriever module.
    Use ?force=true to force.
    """
    try:
        info = ensure_indexes(force_reindex=bool(force))
        return {"status": "ok", "info": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build indexes: {e}")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: Optional[str] = Form("syllabus")):
    """
    Upload PDF/PPTX into DATA_DIR (same dir used by chatbot_retriever.load_all_docs).
    After upload you may call /reindex to include the file.
    """
    from chatbot_retriever import DATA_DIR  # keep using same constant
    os.makedirs(DATA_DIR, exist_ok=True)
    dest_path = os.path.join(DATA_DIR, file.filename)
    try:
        with open(dest_path, "wb") as f:
            content = await file.read()
            f.write(content)
        return {"status": "ok", "filename": file.filename, "saved_to": dest_path}
    except Exception as e:
        logger.exception("upload failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/docs_list")
def docs_list():
    """List files in DATA_DIR (documents available to retriever)."""
    from chatbot_retriever import DATA_DIR
    if not os.path.isdir(DATA_DIR):
        return {"files": []}
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    return {"files": files}


@app.get("/retrieve", response_model=RetrieveResponse)
def retrieve(query: str, subject: Optional[str] = None, top_k: Optional[int] = None):
    """
    Directly call the hybrid retriever for a query. Returns context + meta.
    """
    try:
        # ensure indexes built (but don't force)
        ensure_indexes(force_reindex=False)
        res = hybrid_retrieve(query=query, subject=subject, top_k=(top_k or None))
        return {"query": query, "context": res.get("context"), "meta": res.get("meta", [])}
    except Exception as e:
        logger.exception("retrieve failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{user_id}")
def get_history(user_id: str, limit: Optional[int] = 500):
    """Return persisted history for a user (in same format your frontend expects)."""
    try:
        hist = extract_history_for_frontend(user_id)
        if limit:
            hist = hist[-int(limit):]
        return {"user_id": user_id, "history": hist}
    except Exception as e:
        logger.exception("history fetch failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/clear")
def clear_memory(user_id: str):
    """Clear stored memory for user."""
    try:
        deleted = clear_user_memory(user_id)
        return {"status": "ok", "deleted_rows": deleted}
    except Exception as e:
        logger.exception("clear failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Main chat endpoint.
    - saves user message
    - fetches last messages from sqlite memory
    - runs retriever to get context
    - builds the system prompt + last 3 user messages
    - calls the LLM via call_llm (same wrapper imported from chatbot_graph)
    - saves assistant reply and returns it + updated history
    """
    uid = (req.user_id or os.getenv("DEFAULT_USER", "vinayak")).strip() or "vinayak"
    if not req.message:
        raise HTTPException(status_code=400, detail="message is required")

    try:
        # 1) persist user message
        save_message(uid, "user", req.message)

        # 2) get rows (chronological order) for retriever
        rows = get_last_messages(uid, limit=200)

        # 3) ensure indexes exist (non-force)
        try:
            ensure_indexes(force_reindex=False)
        except Exception:
            logger.warning("Indexes not built or failed. retriever may return no context.")

        # 4) run retrieve_node_from_rows to get context (keeps same logic as your retriever glue)
        try:
            retrieved = retrieve_node_from_rows(rows)
            context = retrieved.get("context")
        except Exception:
            logger.exception("retriever call failed")
            context = None

        # 5) build system prompt content
        # ===== Combine retrieval context + last 2 user turns =====
        MAX_TOKENS_CONTEXT = 3000
        NUM_RECENT_TURNS = 2   # last 2 user + assistant pairs

# Get last few messages (both user + assistant)
        recent_pairs = rows[-(NUM_RECENT_TURNS * 2):]
        recent_chat = "\n".join([f"{r[0].upper()}: {r[1]}" for r in recent_pairs])

# Trim context to token-safe limit
        context_texts = context.split("\n\n") if context else []
        trimmed_context = trim_to_token_limit(context_texts, limit=MAX_TOKENS_CONTEXT)

# Final system prompt
        system_content = SYSTEM_PROMPT
        if trimmed_context:
            system_content += "\n\n===== RETRIEVED CONTEXT =====\n" + trimmed_context

# Always include recent conversation (to maintain chat flow)
        system_content += "\n\n===== RECENT CHAT =====\n" + recent_chat

        # build prompt messages as list of simple dicts (call_llm expects same message format as in chatbot_graph)
        # chatbot_graph.call_llm expects langchain messages (SystemMessage/HumanMessage) — we built that in original file.
        # create messages as minimal objects that call_llm can accept (we rely on original call_llm).
        from langchain_core.messages import SystemMessage, HumanMessage  # re-use same message classes
        prompt_msgs = [SystemMessage(content=system_content)]

        # collect last 3 user messages
        last_users = [r[1] for r in rows if r[0] == "user"][-1:]
        if not last_users:
            last_users = [req.message]
        for u in last_users:
            prompt_msgs.append(HumanMessage(content=u))

        # 6) call LLM
        try:
            raw = call_llm(prompt_msgs)
            answer = _extract_answer_from_response(raw) or ""
        except Exception as e:
            logger.exception("LLM call failed")
            # If LLM client not configured (ChatGroq missing or no API KEY), return helpful message
            detail = str(e)
            answer = f"LLM call failed: {detail}"

        # 7) persist assistant reply
        try:
            save_message(uid, "assistant", answer)
        except Exception:
            logger.exception("Failed to persist assistant message")

        # 8) build history to return
        history = extract_history_for_frontend(uid)
        return {
            "user_id": uid,
            "message": req.message,
            "assistant": answer,
            "history": history,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("chat failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files for frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React frontend for all non-API routes"""
        if full_path and not full_path.startswith("api"):
            file_path = os.path.join(FRONTEND_DIR, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# Run with: uvicorn main_api:app --reload --host 127.0.0.1 --port 8000
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main_api:app", host="0.0.0.0", port=port)
