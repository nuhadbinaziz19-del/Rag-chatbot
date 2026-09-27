from ..db import connect
from .store import _rows


def create_user(email: str, password_hash: str) -> int | None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING RETURNING id",
            (email, password_hash),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_by_email(email: str) -> dict | None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email,))
        rows = _rows(cur)
        return rows[0] if rows else None


def get_by_id(user_id: int) -> dict | None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
        rows = _rows(cur)
        return rows[0] if rows else None
