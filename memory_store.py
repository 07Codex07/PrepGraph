# memory_store.py
import sqlite3
import os
import logging
from typing import List, Tuple

DB_PATH = os.getenv("MEMORY_DB", "chat_memory.db")
MAX_MESSAGES_PER_USER = int(os.getenv("MAX_MESSAGES_PER_USER", 500))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_conn():
    # check_same_thread=False so Gradio threads can use the DB concurrently
    return sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)


def init_db():
    conn = _get_conn()
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
    finally:
        conn.close()


def save_message(user_id: str, role: str, message: str) -> None:
    if not user_id:
        raise ValueError("user_id is required")
    conn = _get_conn()
    try:
        with conn:
            conn.execute(
                "INSERT INTO memory (user_id, role, message) VALUES (?, ?, ?)",
                (user_id, role, message),
            )
            # prune if too many
            if MAX_MESSAGES_PER_USER and MAX_MESSAGES_PER_USER > 0:
                cur = conn.execute(
                    "SELECT id FROM memory WHERE user_id = ? ORDER BY id DESC",
                    (user_id,),
                )
                rows = cur.fetchall()
                if len(rows) > MAX_MESSAGES_PER_USER:
                    ids_to_delete = [r[0] for r in rows[MAX_MESSAGES_PER_USER:]]
                    conn.executemany("DELETE FROM memory WHERE id = ?", [(i,) for i in ids_to_delete])
    except Exception:
        logger.exception("Failed to save message for user %s", user_id)
        raise
    finally:
        conn.close()


def get_last_messages(user_id: str, limit: int = 200) -> List[Tuple[str, str, str]]:
    """
    Return last `limit` messages in chronological order as (role, message, created_at)
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT role, message, created_at FROM memory
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()
        return list(reversed(rows))
    except Exception:
        logger.exception("Failed to fetch messages for user %s", user_id)
        return []
    finally:
        conn.close()


def clear_user_memory(user_id: str) -> int:
    """Delete memory for user. Returns deleted rowcount."""
    conn = _get_conn()
    try:
        with conn:
            cur = conn.execute("DELETE FROM memory WHERE user_id = ?", (user_id,))
            return cur.rowcount
    except Exception:
        logger.exception("Failed to clear memory for user %s", user_id)
        raise
    finally:
        conn.close()


def build_gradio_history(user_id: str) -> List[dict]:
    """
    Return history formatted for gr.Chatbot with type='messages':
    A chronological list of dicts: {'role':'user'|'assistant','content': '...'}
    """
    rows = get_last_messages(user_id, limit=500)
    return [{"role": r[0], "content": r[1]} for r in rows]
