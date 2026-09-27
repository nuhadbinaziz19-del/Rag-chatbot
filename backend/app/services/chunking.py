"""Sentence-aware chunking. Handles the Bangla danda (।) as a sentence end."""
import re

_SENTENCE_END = re.compile(r"(?<=[।.!?])\s+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("require 0 <= overlap < size")

    units: list[str] = []
    for s in split_sentences(text):
        units.extend(s[i : i + size] for i in range(0, len(s), size))

    chunks: list[str] = []
    cur: list[str] = []
    n = 0
    for u in units:
        if cur and n + len(u) + 1 > size:
            chunks.append(" ".join(cur))
            tail: list[str] = []
            t = 0
            for x in reversed(cur):  # carry trailing sentences as overlap
                if t + len(x) > overlap:
                    break
                tail.insert(0, x)
                t += len(x) + 1
            cur, n = tail, t
        cur.append(u)
        n += len(u) + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks
