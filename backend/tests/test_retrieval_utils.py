from app.services.fusion import rrf
from app.services.prompt import build_messages, sources_payload
from app.services.text_utils import tokenize

CHUNK = {"filename": "a.pdf", "page": 3, "content": "ঢাকা বাংলাদেশের রাজধানী।", "document_id": 1, "score": 0.91234}


def test_tokenize_keeps_bangla_vowel_signs():
    assert tokenize("বাংলাদেশের রাজধানী ঢাকা।") == ["ঢাকা", "বাংলাদেশের", "রাজধানী"]


def test_tokenize_english_and_short_tokens():
    assert tokenize("A RAG system, 2026!") == ["2026", "rag", "system"]


def test_rrf_rewards_agreement_between_rankers():
    order = rrf([[1, 2, 3], [3, 2, 4]])
    assert set(order[:2]) == {2, 3}
    assert order[-1] == 4


def test_messages_end_with_cited_context_question():
    msgs = build_messages("রাজধানী কী?", [CHUNK], [])
    assert msgs[-1]["role"] == "user"
    assert "[1] (a.pdf, page 3)" in msgs[-1]["content"]


def test_history_is_normalized_to_alternating_roles():
    history = [
        {"role": "assistant", "content": "orphan"},
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "dangling"},
    ]
    msgs = build_messages("q2", [CHUNK], history)
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]


def test_sources_payload_shape():
    src = sources_payload([CHUNK])[0]
    assert src["n"] == 1 and src["page"] == 3 and src["score"] == 0.9123
