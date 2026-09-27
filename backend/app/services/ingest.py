from ..config import settings
from .chunking import chunk_text
from .embeddings import embed_passages
from .extract import extract_pages
from .store import add_document


def ingest_pdf(user_id: int, filename: str, data: bytes) -> dict:
    pages = extract_pages(data)
    if not pages:
        raise ValueError("No readable text found in this PDF (even after OCR).")

    rows: list[tuple[int, int, str]] = []
    for page in pages:
        for i, chunk in enumerate(chunk_text(page.text, settings.chunk_size, settings.chunk_overlap)):
            rows.append((page.number, i, chunk))

    vectors = embed_passages([r[2] for r in rows])
    doc_id = add_document(user_id, filename, len(pages), rows, vectors)
    return {
        "id": doc_id,
        "filename": filename,
        "pages": len(pages),
        "chunks": len(rows),
        "ocr_pages": sum(p.ocr for p in pages),
    }
