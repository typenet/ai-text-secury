"""Orquestra o scan: detecta o formato, roda o extrator e os detectores transversais."""

from __future__ import annotations

from enum import StrEnum

from app.scanner import docx, injection, lgpd, txt, unicode
from app.scanner.findings import ExtractionResult
from app.scanner.report import ScanReport, build_report

ENGINE_VERSION = "0.1.0"


class DocType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class UnsupportedDocument(ValueError):
    pass


def detect_type(data: bytes, filename: str | None = None) -> DocType:
    """Detecta pelo conteúdo (magic bytes), não pela extensão informada pelo cliente."""
    if data[:5] == b"%PDF-" or b"%PDF-" in data[:1024]:
        return DocType.PDF
    if data[:4] == b"PK\x03\x04":
        if b"word/" in data[:4096] or (filename or "").lower().endswith(".docx"):
            return DocType.DOCX
        raise UnsupportedDocument("arquivo ZIP que não parece DOCX")
    if b"\x00" not in data[:4096] or data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return DocType.TXT
    raise UnsupportedDocument("formato não suportado")


def _extract(doc_type: DocType, data: bytes) -> ExtractionResult:
    if doc_type is DocType.PDF:
        from app.scanner import pdf  # import tardio: pdfplumber/pikepdf são pesados

        return pdf.extract(data)
    if doc_type is DocType.DOCX:
        return docx.extract(data)
    return txt.extract(data)


def scan_bytes(data: bytes, filename: str | None = None) -> ScanReport:
    doc_type = detect_type(data, filename)
    result = _extract(doc_type, data)

    # Unicode invisível em todos os segmentos (pode revelar texto escondido em tags).
    for seg in list(result.segments):
        findings, hidden = unicode.scan_segment(seg)
        result.findings.extend(findings)
        if hidden:
            result.segments.append(hidden)

    result.findings.extend(injection.scan_segments(result.segments))
    result.findings.extend(lgpd.scan_segments([s for s in result.segments if not s.hidden]))

    return build_report(result.findings, result.page_count, ENGINE_VERSION)
