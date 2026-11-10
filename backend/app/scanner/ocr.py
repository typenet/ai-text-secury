"""Render + OCR, acionado só nas páginas suspeitas.

Ideia (PhantomLint): renderizar a página (pypdfium2), rodar OCR (Tesseract `por+eng`) e
comparar com o texto extraído. Texto extraído que não aparece no OCR = texto que o humano
não vê (coberto por imagem, cor do fundo real, fonte maliciosa).
"""

from __future__ import annotations

import difflib
import logging

from app.scanner.findings import Finding
from app.scanner.rules import rule

log = logging.getLogger(__name__)
VERSION = "ocr@0.1.0"


def ocr_page(data: bytes, page_index: int, scale: float = 2.0, lang: str = "por+eng") -> str:
    import pypdfium2 as pdfium
    import pytesseract

    pdf = pdfium.PdfDocument(data)
    try:
        image = pdf[page_index].render(scale=scale).to_pil()
        return pytesseract.image_to_string(image, lang=lang)
    finally:
        pdf.close()


def invisible_words(extracted: str, ocr_text: str) -> list[str]:
    """Palavras do texto extraído que não aparecem no OCR."""
    a = extracted.lower().split()
    b = ocr_text.lower().split()
    missing: list[str] = []
    for tag, i1, i2, _, _ in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag in ("delete", "replace"):
            missing.extend(a[i1:i2])
    return missing


def check_page(data: bytes, page_number: int, extracted: str, min_words: int = 5) -> list[Finding]:
    try:
        ocr_text = ocr_page(data, page_number - 1)
    except Exception:  # Tesseract ausente, página corrompida etc.
        log.exception("OCR falhou na página %s", page_number)
        return []
    missing = invisible_words(extracted, ocr_text)
    if len(missing) < min_words:
        return []
    r = rule("TEXT_UNDER_IMAGE")
    return [
        Finding(
            rule=r.code,
            severity=r.severity,
            page=page_number,
            text=" ".join(missing)[:500],
            confidence=60,
            technique=r.technique,
            detector_version=VERSION,
            evidence={"missing_words": len(missing)},
        )
    ]
