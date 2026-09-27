from functools import lru_cache

from sentence_transformers import CrossEncoder

from ..config import settings


@lru_cache(maxsize=1)
def _model() -> CrossEncoder:
    return CrossEncoder(settings.reranker_model)


def rerank(query: str, chunks: list[dict]) -> list[dict]:
    if not chunks:
        return chunks
    scores = _model().predict([(query, c["content"]) for c in chunks])
    for c, s in zip(chunks, scores):
        c["score"] = float(s)
    return sorted(chunks, key=lambda c: c["score"], reverse=True)
