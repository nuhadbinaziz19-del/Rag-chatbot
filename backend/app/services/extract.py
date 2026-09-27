"""PDF text extraction with OCR fallback (Bangla + English)."""
import io
import re
import unicodedata
from dataclasses import dataclass

import fitz  # PyMuPDF

from ..config import settings


@dataclass
class Page:
    number: int
    text: str
    ocr: bool = False


def normalize(text: str) -> str:
    # NFC keeps Bangla conjuncts consistent; ZWJ/ZWNJ are intentionally preserved.
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()


def _looks_broken(text: str) -> bool:
    """Legacy Bangla fonts often extract as garbage (U+FFFD / cid refs)."""
    if not text:
        return True
    bad = text.count("\ufffd") + text.count("(cid:") * 6
    return bad / max(len(text), 1) > 0.05


def _ocr(page: "fitz.Page") -> str:
    try:
        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang=settings.ocr_langs).strip()
    except Exception:
        return ""


def extract_pages(data: bytes) -> list[Page]:
    pages: list[Page] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for i, p in enumerate(doc, start=1):
            text = p.get_text("text").strip()
            used_ocr = False
            if len(text) < settings.min_text_chars_per_page or _looks_broken(text):
                ocr_text = _ocr(p)
                if ocr_text:
                    text, used_ocr = ocr_text, True
            text = normalize(text)
            if text:
                pages.append(Page(i, text, used_ocr))
    return pages
