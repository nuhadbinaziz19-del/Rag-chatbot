import json

from ..db import connect
from .store import _rows


def create_conversation(user_id: int, title: str) -> int:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING id", (user_id, title[:80])
        )
        return cur.fetchone()[0]


def conversation_exists(conv_id: int, user_id: int) -> bool:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM conversations WHERE id = %s AND user_id = %s", (conv_id, user_id))
        return cur.fetchone() is not None


def get_history(conv_id: int, limit: int) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT role, content FROM (SELECT id, role, content FROM messages WHERE conversation_id = %s"
            " ORDER BY id DESC LIMIT %s) t ORDER BY id",
            (conv_id, limit),
        )
        return _rows(cur)


def add_exchange(conv_id: int, question: str, answer: str, sources: list[dict]) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (%s, 'user', %s)", (conv_id, question)
        )
        cur.execute(
            "INSERT INTO messages (conversation_id, role, content, sources) VALUES (%s, 'assistant', %s, %s)",
            (conv_id, answer, json.dumps(sources, ensure_ascii=False)),
        )


def list_conversations(user_id: int) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, created_at FROM conversations WHERE user_id = %s ORDER BY id DESC", (user_id,)
        )
        return _rows(cur)


def get_messages(conv_id: int) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, role, content, sources, created_at FROM messages WHERE conversation_id = %s ORDER BY id",
            (conv_id,),
        )
        return _rows(cur)


def delete_conversation(conv_id: int, user_id: int) -> bool:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM conversations WHERE id = %s AND user_id = %s", (conv_id, user_id))
        return cur.rowcount > 0
