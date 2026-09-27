import pytest

from app.services.chunking import chunk_text, split_sentences


def test_bangla_danda_splits_sentences():
    assert split_sentences("আমি ভাত খাই। তুমি কী খাও? ভালো!") == ["আমি ভাত খাই।", "তুমি কী খাও?", "ভালো!"]


def test_chunks_respect_size_and_overlap():
    text = " ".join(f"This is sentence number {i}." for i in range(200))
    chunks = chunk_text(text, size=300, overlap=60)
    assert len(chunks) > 1
    assert all(len(c) <= 300 + 60 for c in chunks)
    tail = chunks[0].split(". ")[-1][:15]
    assert tail in chunks[1]  # overlap carried over


def test_long_sentence_is_hard_split():
    assert len(chunk_text("a" * 2500, size=900, overlap=100)) >= 3


def test_invalid_params():
    with pytest.raises(ValueError):
        chunk_text("x", size=100, overlap=100)
