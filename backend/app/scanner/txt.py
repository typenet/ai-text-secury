"""Extrator de TXT: decodifica e entrega o texto como um único segmento visível."""

from __future__ import annotations

from app.scanner.findings import ExtractionResult, TextSegment


def decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16"):
        try:
            text = data.decode(enc)
            if enc == "utf-16" and "\x00" in text:
                continue
            return text
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def extract(data: bytes) -> ExtractionResult:
    return ExtractionResult(segments=[TextSegment(decode(data), page=1)], page_count=1)
