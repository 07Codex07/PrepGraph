from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from typing import TypedDict, Annotated, Optional
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

# RAG deps
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.powerpoint import UnstructuredPowerPointLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

import os
import re
from collections import defaultdict

# -----------------------------
# Config
# -----------------------------
MAX_CONTEXT_CHARS = 1000   # cap retrieved notes per turn (only for LLM context)
TOP_K_DOCS = 2             # limit retrieved docs

# -----------------------------
# Init
# -----------------------------
load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # updated model
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY"),
)

class Chatbot(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: Optional[str]
    direct: Optional[bool]  # True when we should bypass LLM and return context directly


# -----------------------------
# Helpers: subject & year parsing
# -----------------------------
SUBJECT_KEYS = {
    "cn": {"cn", "computer network", "computer networks"},
    "dos": {"dos", "operating system", "os", "distributed os"},
    "se": {"se", "software engineering"}
}

def detect_subject(text: str) -> Optional[str]:
    t = text.lower()
    for subj, keys in SUBJECT_KEYS.items():
        for k in keys:
            if k in t:
                return subj
    # filename-style hints (e.g., startswith)
    if t.strip().startswith("cn"):
        return "cn"
    if t.strip().startswith("dos"):
        return "dos"
    if t.strip().startswith("se"):
        return "se"
    return None

def extract_year(s: str) -> Optional[str]:
    # Find a 4-digit year from 2000..2099
    m = re.search(r"\b(20\d{2})\b", s)
    return m.group(1) if m else None



# Load documents with metadata

def load_all_docs(base_dir: str = "data"):
    """
    Loads:
      - syllabus PDFs in data/ (cn.pdf, dos.pdf, se.pdf)
      - PYQ PDFs in data/pyqs/*.pdf
      - PPTX in data/ (optional)
    Adds metadata:
      - subject: cn/dos/se (best-effort from filename)
      - filename
      - category: 'syllabus' or 'pyq'
      - year: parsed from filename when present (e.g., *_2019.pdf)
    """
    all_docs = []

    if not os.path.isdir(base_dir):
        return all_docs

    # 1) Load syllabus PDFs and PPTX from root of data/
    for file in os.listdir(base_dir):
        path = os.path.join(base_dir, file)
        if not os.path.isfile(path):
            continue

        fname = file.lower()
        try:
            if fname.endswith(".pdf"):
                loader = PyPDFLoader(path)
                category = "syllabus"
            elif fname.endswith(".pptx"):
                loader = UnstructuredPowerPointLoader(path)
                category = "syllabus"
            else:
                continue

            file_docs = loader.load()
            subject = detect_subject(fname)
            year = extract_year(fname)

            for d in file_docs:
                d.metadata["subject"] = subject
                d.metadata["filename"] = file
                d.metadata["category"] = category
                if year:
                    d.metadata["year"] = year

            all_docs.extend(file_docs)

        except Exception as e:
            print(f"[load_all_docs] Skipped {file}: {e}")

    # 2) Load PYQs from data/pyqs
    pyqs_dir = os.path.join(base_dir, "pyqs")
    if os.path.isdir(pyqs_dir):
        for file in os.listdir(pyqs_dir):
            path = os.path.join(pyqs_dir, file)
            if not os.path.isfile(path):
                continue

            fname = file.lower()
            if not fname.endswith(".pdf"):
                continue

            try:
                loader = PyPDFLoader(path)
                file_docs = loader.load()

                subject = detect_subject(fname) or _guess_subject_from_filename(fname)
                year = extract_year(fname)

                for d in file_docs:
                    d.metadata["subject"] = subject
                    d.metadata["filename"] = file
                    d.metadata["category"] = "pyq"
                    d.metadata["year"] = year if year else None
                    # also keep source path for future use if needed
                    d.metadata["source_path"] = path

                all_docs.extend(file_docs)

            except Exception as e:
                print(f"[load_all_docs] Skipped PYQ {file}: {e}")

    return all_docs

def _guess_subject_from_filename(fname: str) -> Optional[str]:
    # Simple prefix-based guess
    if fname.startswith("cn"):
        return "cn"
    if fname.startswith("dos"):
        return "dos"
    if fname.startswith("se"):
        return "se"
    # fallback: look for words
    return detect_subject(fname)


docs = load_all_docs()

# Build a mapping of pages per file for direct "full paper" returns
# { (subject, year, filename) : [Document(page0), Document(page1), ...] }
docs_by_file = defaultdict(list)
for d in docs:
    key = (d.metadata.get("subject"), d.metadata.get("year"), d.metadata.get("filename"))
    docs_by_file[key].append(d)

# Split & index for RAG (LLM path)
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = splitter.split_documents(docs) if docs else []

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embeddings) if chunks else None



# Smart retrieval

def build_direct_pyq_text(subject: str, year: Optional[str]) -> Optional[str]:
    """
    Assemble full PYQ text for a subject (and optionally a specific year).
    Returns a single big string containing the paper(s) in page order.
    """
    # Collect matching files (category == pyq, subject matches, and if year given, year matches)
    # We iterate docs_by_file to keep page ordering within each file.
    collected_texts = []

    for (subj, y, filename), pages in docs_by_file.items():
        # only pyq files
        # pages share the same metadata, so check category on first page
        if not pages:
            continue
        if pages[0].metadata.get("category") != "pyq":
            continue
        if subj != subject:
            continue
        if year and (y != year):
            continue

        # Sort pages by the 'page' metadata if present
        try:
            pages_sorted = sorted(pages, key=lambda p: p.metadata.get("page", 0))
        except Exception:
            pages_sorted = pages

        text = "\n".join(p.page_content for p in pages_sorted if p.page_content)
        if text.strip():
            header = f"\n\n===== {filename} =====\n"
            collected_texts.append(header + text)

    if not collected_texts:
        return None

    return "\n".join(collected_texts).strip()


def smart_retrieve(query: str):
    """
    1) If query requests a FULL PYQ / FULL QUESTION PAPER:
        - detect subject and optional year
        - return full text directly (no LLM)
    2) Else:
        - do semantic search; if subject is in query, filter by subject
        - return small context (capped) for LLM
    """
    if not docs:
        return {"context": None, "direct": False}

    q = query.lower()

    # Heuristics for "full paper" requests
    wants_full = any(k in q for k in ["full", "entire", "complete"])
    mentions_paper = any(k in q for k in ["pyq", "question paper", "paper", "past year"])
    if wants_full and mentions_paper:
        subject = detect_subject(q)
        year = extract_year(q)
        if subject:
            direct_text = build_direct_pyq_text(subject, year)
            if direct_text:
                return {"context": direct_text, "direct": True}

    # Otherwise → normal semantic retrieval (subject-filtered)
    subject = detect_subject(q)
    if vectorstore:
        try:
            if subject:
                # Use FAISS similarity_search with metadata filter for exact subject match
                results = vectorstore.similarity_search(
                    query, k=TOP_K_DOCS, filter={"subject": subject}
                )
            else:
                results = vectorstore.similarity_search(query, k=TOP_K_DOCS)
        except Exception as e:
            print(f"[vectorstore] error: {e}")
            return {"context": None, "direct": False}
    else:
        results = []

    if not results:
        return {"context": None, "direct": False}

    ctx = "\n\n".join(r.page_content for r in results if r.page_content).strip()
    if not ctx:
        return {"context": None, "direct": False}

    if len(ctx) > MAX_CONTEXT_CHARS:
        ctx = ctx[:MAX_CONTEXT_CHARS] + "..."
    return {"context": ctx, "direct": False}


# -----------------------------
# Graph nodes
# -----------------------------
def _last_two_user_messages(messages: list[BaseMessage]) -> list[HumanMessage]:
    users: list[HumanMessage] = []
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            users.append(m)
            if len(users) == 2:
                break
    users.reverse()
    return users


def retrieve_node(state: Chatbot):
    last_users = _last_two_user_messages(state["messages"])
    current_query = last_users[-1].content if last_users else ""
    result = smart_retrieve(current_query) if current_query else {"context": None, "direct": False}
    return {"context": result["context"], "direct": result["direct"]}


def chat_node(state: Chatbot):
    # If we have a direct payload (full PYQ), return it without calling the LLM.
    if state.get("direct") and state.get("context"):
        return {"messages": [AIMessage(content=state["context"])], "context": None, "direct": None}

    # Otherwise, construct a small prompt with retrieved context + the last user turns
    prompt: list[BaseMessage] = []
    if state.get("context"):
        prompt.append(SystemMessage(content=f"Use these notes to answer succinctly and accurately:\n{state['context']}"))

    last_users = _last_two_user_messages(state["messages"])
    if not last_users and state["messages"]:
        last = state["messages"][-1]
        if isinstance(last, BaseMessage):
            last_users = [last]  # type: ignore

    prompt.extend(last_users)

    response = llm.invoke(prompt)
    return {"messages": [response], "context": None, "direct": None}


# -----------------------------
# Graph
# -----------------------------
checkpointer = InMemorySaver()
graph = StateGraph(Chatbot)
graph.add_node("retrieve", retrieve_node)
graph.add_node("chat", chat_node)

graph.add_edge(START, "retrieve")
graph.add_edge("retrieve", "chat")
graph.add_edge("chat", END)

chatbot = graph.compile(checkpointer=checkpointer)
