from collections.abc import Iterator
from functools import lru_cache

from anthropic import Anthropic

from ..config import settings


@lru_cache(maxsize=1)
def _client() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)


def condense_question(question: str, history: list[dict]) -> str:
    """Rewrite a follow-up ("what about page 2?") into a standalone search query."""
    if not history:
        return question
    transcript = "\n".join(f"{m['role']}: {m['content'][:500]}" for m in history[-4:])
    try:
        r = _client().messages.create(
            model=settings.llm_model,
            max_tokens=200,
            system="Rewrite the user's last message as a standalone search query, using the conversation for "
            "context. Keep the same language. Output only the query.",
            messages=[{"role": "user", "content": f"{transcript}\nuser: {question}"}],
        )
        return r.content[0].text.strip() or question
    except Exception:
        return question


def stream_answer(system: str, messages: list[dict]) -> Iterator[str]:
    with _client().messages.stream(
        model=settings.llm_model, max_tokens=settings.llm_max_tokens, system=system, messages=messages
    ) as stream:
        yield from stream.text_stream
