import numpy as np

from ..db import connect
from .text_utils import tokenize


def add_document(user_id: int, filename: str, n_pages: int, rows: list[tuple[int, int, str]], vectors: np.ndarray) -> int:
    """rows: (page, chunk_index, content) aligned with vectors."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO documents (user_id, filename, n_pages, n_chunks) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, filename, n_pages, len(rows)),
        )
        doc_id = cur.fetchone()[0]
        cur.executemany(
            "INSERT INTO chunks (document_id, page, chunk_index, content, embedding, tokens)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            [(doc_id, pg, idx, txt, vec, tokenize(txt)) for (pg, idx, txt), vec in zip(rows, vectors)],
        )
    return doc_id


def _rows(cur) -> list[dict]:
    cols = [c.name for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def search_vector(query_vec: np.ndarray, k: int, user_id: int, doc_ids: list[int] | None = None) -> list[dict]:
    sql = """
        SELECT c.id, c.content, c.page, c.document_id, d.filename,
               (1 - (c.embedding <=> %(v)s))::float AS score
        FROM chunks c JOIN documents d ON d.id = c.document_id
        WHERE d.user_id = %(uid)s AND (%(docs)s::int[] IS NULL OR c.document_id = ANY(%(docs)s))
        ORDER BY c.embedding <=> %(v)s
        LIMIT %(k)s
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, {"v": query_vec, "uid": user_id, "docs": doc_ids, "k": k})
        return _rows(cur)


def search_keyword(tokens: list[str], k: int, user_id: int, doc_ids: list[int] | None = None) -> list[dict]:
    """Token-overlap search. Uses a GIN index on tokens; works for Bangla where Postgres FTS is unreliable."""
    if not tokens:
        return []
    sql = """
        SELECT c.id, c.content, c.page, c.document_id, d.filename,
               (SELECT count(*) FROM unnest(c.tokens) t WHERE t = ANY(%(q)s))::float AS score
        FROM chunks c JOIN documents d ON d.id = c.document_id
        WHERE d.user_id = %(uid)s AND c.tokens && %(q)s::text[]
          AND (%(docs)s::int[] IS NULL OR c.document_id = ANY(%(docs)s))
        ORDER BY score DESC
        LIMIT %(k)s
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, {"q": tokens, "uid": user_id, "docs": doc_ids, "k": k})
        return _rows(cur)


def list_documents(user_id: int) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, filename, n_pages, n_chunks, created_at FROM documents WHERE user_id = %s ORDER BY id DESC",
            (user_id,),
        )
        return _rows(cur)


def count_documents(user_id: int) -> int:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM documents WHERE user_id = %s", (user_id,))
        return cur.fetchone()[0]


def delete_document(doc_id: int, user_id: int) -> bool:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE id = %s AND user_id = %s", (doc_id, user_id))
        return cur.rowcount > 0
