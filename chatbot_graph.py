# chatbot_graph.py
import os
from dotenv import load_dotenv
import gradio as gr
import logging
from typing import List

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# LLM client (Groq wrapper)
try:
    from langchain_groq import ChatGroq
except Exception:
    ChatGroq = None
    logger.warning("langchain_groq.ChatGroq not importable. Ensure langchain-groq is installed in requirements.")

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from chatbot_retriever import retrieve_node_from_rows
from memory_store import init_db, save_message, get_last_messages, build_gradio_history

# initialize DB early
init_db()

# Instantiate Groq LLM (will require GROQ_API_KEY in env)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", None)
GROQ_TEMP = float(os.getenv("GROQ_TEMP", "0.2"))

if ChatGroq:
    llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=GROQ_TEMP)
else:
    llm = None


def _extract_answer_from_response(response):
    # robust extraction similar to your previous helper - simplified
    try:
        if hasattr(response, "content"):
            c = response.content
            if isinstance(c, str) and c.strip():
                return c.strip()
            if isinstance(c, (list, tuple)):
                parts = [str(x) for x in c if x is not None]
                if parts:
                    return "".join(parts).strip()
            if isinstance(c, dict):
                for key in ("answer", "text", "content", "output_text", "generated_text"):
                    v = c.get(key)
                    if v:
                        if isinstance(v, (list, tuple)):
                            return "".join([str(x) for x in v]).strip()
                        return str(v).strip()
        if isinstance(response, dict):
            for key in ("answer", "text", "content"):
                v = response.get(key)
                if v:
                    return str(v)
            choices = response.get("choices") or response.get("outputs")
            if isinstance(choices, (list, tuple)) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get("message") or first.get("text") or first.get("content")
                    if msg:
                        if isinstance(msg, (list, tuple)):
                            return "".join([str(x) for x in msg])
                        return str(msg)
        if hasattr(response, "generations"):
            gens = getattr(response, "generations")
            if gens:
                for outer in gens:
                    for g in outer:
                        if hasattr(g, "text") and g.text:
                            return str(g.text)
                        if hasattr(g, "message") and getattr(g.message, "content", None):
                            return str(g.message.content)
        s = str(response)
        if s and s.strip():
            return s.strip()
    except Exception:
        logger.exception("Failed extracting answer")
    return None


SYSTEM_PROMPT = (
    "You are PrepGraph — an accurate, concise AI tutor specialized for academic content.\n"
    "Rules:\n"
    "1) Prefer the provided CONTEXT (delimited below) when answering. Cite which doc (filename) or say 'from provided context' where applicable.\n"
    "2) Use the user's last 3 queries to understand intent and keep answers consistent.\n"
    "3) If the context directly answers the question, answer from it and show the short excerpt.\n"
    "4) If you are uncertain, say you are unsure and suggest what additional info is needed.\n"
    "5) Keep answers clear, step-by-step when asked, and avoid hallucination.\n\n"
    "CONTEXT:\n"
)

# ---- helper: call the LLM with a list of messages (SystemMessage + HumanMessage...) ----
def call_llm(messages: List):
    if not llm:
        raise RuntimeError("LLM client (ChatGroq) not configured or import failed. Set up langchain_groq and GROQ_API_KEY.")
    # many wrappers accept the langchain message objects; keep using llm.invoke
    response = llm.invoke(messages)
    return response


# ---- Gradio UI functions ----
def load_history(user_id: str):
    uid = (user_id or os.getenv("DEFAULT_USER", "vinayak")).strip() or "vinayak"
    try:
        hist = build_gradio_history(uid)
        logger.info("Loaded %d messages for user %s", len(hist), uid)
        return hist
    except Exception:
        logger.exception("Failed to load history for %s", uid)
        return []


def chat_interface(user_input: str, chat_state: List[dict], user_id: str):
    """
    Receives user_input (string), chat_state (list of {'role':..., 'content':...}),
    user_id (string). Returns: (clear_input_str, new_chat_state)
    """
    uid = (user_id or os.getenv("DEFAULT_USER", "vinayak")).strip() or "vinayak"
    history = chat_state or []

    # Save user's message immediately
    try:
        save_message(uid, "user", user_input)
    except Exception:
        logger.exception("Failed to persist user message")

    # Build rows to pass to retriever: get last messages from DB (ensures persistence)
    rows = get_last_messages(uid, limit=200)  # chronological order

    # Retrieve context using hybrid retriever (uses last 3 user messages internally)
    try:
        retrieved = retrieve_node_from_rows(rows)
        context = retrieved.get("context")
    except Exception:
        logger.exception("Retriever failed")
        context = None

    # Build prompt: SystemMessage + last 3 user messages (HumanMessage)
    prompt_msgs = []
    system_content = SYSTEM_PROMPT + (context or "No context found.")
    prompt_msgs.append(SystemMessage(content=system_content))

    # collect last 3 user messages (from rows)
    last_users = [r[1] for r in rows if r[0] == "user"][-3:]
    if not last_users:
        # fallback to current input if DB empty
        last_users = [user_input]
    # append each of the last user messages as HumanMessage (preserves order)
    for u in last_users:
        prompt_msgs.append(HumanMessage(content=u))

    # send to LLM
    try:
        raw = call_llm(prompt_msgs)
        answer = _extract_answer_from_response(raw) or ""
    except Exception as e:
        logger.exception("LLM call failed")
        answer = f"Sorry — I couldn't process that right now ({e})."

    # persist assistant reply
    try:
        save_message(uid, "assistant", answer)
    except Exception:
        logger.exception("Failed to persist assistant message")

    # update gradio chat state: append current user and assistant
    history = history or load_history(uid)  # in case front-end was empty, rehydrate
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": answer})

    # return: clear the input box (""), updated history for gr.Chatbot(type="messages")
    return "", history


# ---- Minimal / attractive Gradio UI ----
with gr.Blocks(css=".gradio-container {max-width:900px; margin:0 auto;}") as demo:
    gr.Markdown("# 🤖 PrepGraph — RAG Tutor")
    with gr.Row():
        user_id_input = gr.Textbox(label="User ID (will be used to persist your memory)", value=os.getenv("DEFAULT_USER", "vinayak"))
    chatbot = gr.Chatbot(label="Conversation", type="messages")

    with gr.Row():
        msg = gr.Textbox(placeholder="Ask anything about your course material...", show_label=False)
        send = gr.Button("Send")

    with gr.Row():
        clear_ui = gr.Button("Clear Chat")

    # Load history at page load (and when user_id changes)
    demo.load(load_history, [user_id_input], [chatbot])
    user_id_input.change(load_history, [user_id_input], [chatbot])

    # Bind send
    msg.submit(chat_interface, [msg, chatbot, user_id_input], [msg, chatbot])
    send.click(chat_interface, [msg, chatbot, user_id_input], [msg, chatbot])

    # just clears the UI, not the DB
    clear_ui.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
