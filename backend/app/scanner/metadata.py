"""Regras de contêiner do PDF: metadados, JavaScript, OpenAction, anexos, camadas, anotações."""

from __future__ import annotations

import pikepdf

from app.scanner.findings import ExtractionResult, Finding, TextSegment
from app.scanner.rules import rule

VERSION = "pdf-meta@0.1.0"
META_SUSPICIOUS_LEN = 300
ANNOT_FLAG_HIDDEN = 1 << 1  # bit 2
ANNOT_FLAG_NOVIEW = 1 << 5  # bit 6
MAX_OBJECTS = 200_000


def _finding(code: str, text: str = "", page: int | None = None, **evidence) -> Finding:
    r = rule(code)
    return Finding(
        rule=r.code,
        severity=r.severity,
        text=text[:500],
        page=page,
        technique=r.technique,
        detector_version=VERSION,
        evidence=evidence,
    )


def _has_key(obj: pikepdf.Object, key: str) -> bool:
    return isinstance(obj, pikepdf.Dictionary) and key in obj


def scan(pdf: pikepdf.Pdf) -> ExtractionResult:
    out = ExtractionResult(page_count=len(pdf.pages))
    root = pdf.Root

    # Metadados do /Info
    for key, value in (pdf.docinfo or {}).items():
        text = str(value).strip()
        if not text:
            continue
        out.segments.append(TextSegment(text, hidden=True, source=f"metadata{key}"))
        if len(text) > META_SUSPICIOUS_LEN:
            out.findings.append(_finding("SUSPICIOUS_METADATA", text, field=str(key)))

    # Ações automáticas
    if "/OpenAction" in root or "/AA" in root:
        out.findings.append(
            _finding("OPEN_ACTION", keys=[k for k in ("/OpenAction", "/AA") if k in root])
        )

    # JavaScript e anexos na árvore de nomes
    names = root.get("/Names")
    if _has_key(names, "/JavaScript"):
        out.findings.append(_finding("EMBEDDED_JAVASCRIPT", location="/Names/JavaScript"))
    if _has_key(names, "/EmbeddedFiles"):
        out.findings.append(_finding("EMBEDDED_FILE", location="/Names/EmbeddedFiles"))

    # Varredura de objetos para /JS soltos (ex.: em ações de anotação)
    js_count = 0
    for i, obj in enumerate(pdf.objects):
        if i > MAX_OBJECTS:
            break
        if _has_key(obj, "/JS"):
            js_count += 1
    if js_count and not any(f.rule == "EMBEDDED_JAVASCRIPT" for f in out.findings):
        out.findings.append(_finding("EMBEDDED_JAVASCRIPT", objects=js_count))

    # Camadas opcionais desligadas
    ocp = root.get("/OCProperties")
    if _has_key(ocp, "/D"):
        off = ocp.D.get("/OFF")
        if isinstance(off, pikepdf.Array) and len(off):
            layer_names = [str(o.get("/Name", "")) for o in off]
            out.findings.append(
                _finding("HIDDEN_LAYER", ", ".join(layer_names), layers=layer_names)
            )
            # TODO: extrair o texto marcado com /OC dessas camadas como segmento oculto.

    # Anotações e campos de formulário ocultos
    for pno, page in enumerate(pdf.pages, start=1):
        for annot in page.get("/Annots") or []:
            if not isinstance(annot, pikepdf.Dictionary):
                continue
            flags = int(annot.get("/F", 0))
            hidden = bool(flags & (ANNOT_FLAG_HIDDEN | ANNOT_FLAG_NOVIEW))
            subtype = str(annot.get("/Subtype", ""))
            contents = str(annot.get("/Contents", "") or annot.get("/V", "") or "")
            if contents:
                out.segments.append(
                    TextSegment(contents, page=pno, hidden=True, source=f"annot{subtype}")
                )
            if not hidden:
                continue
            code = "HIDDEN_FORM_FIELD" if subtype == "/Widget" else "HIDDEN_COMMENT"
            out.findings.append(_finding(code, contents, page=pno, subtype=subtype, flags=flags))
    return out
