"""Extrator + regras estruturais de PDF (pdfplumber + pikepdf; sem PyMuPDF por ser AGPL).

Passos por página:
1. pdfplumber: palavras com tamanho e cor -> TINY_FONT, WHITE_TEXT, OFF_PAGE_TEXT.
2. pikepdf: content stream -> TRANSPARENT_TEXT (Tr 3 ou ExtGState com ca/CA = 0).
3. metadata.scan: JavaScript, OpenAction, anexos, camadas, anotações, metadados.
Render/OCR (ocr.py) fica para as páginas suspeitas; ainda não está ligado ao fluxo.
"""

from __future__ import annotations

import io
from collections.abc import Iterable
from typing import Any

import pdfplumber
import pikepdf

from app.scanner import metadata
from app.scanner.findings import ExtractionResult, Finding, TextSegment
from app.scanner.rules import rule

VERSION = "pdf@0.1.0"
TINY_FONT_PT = 2.0
WHITE_THRESHOLD = 0.95
OFF_PAGE_MARGIN = 1.0
MAX_PAGES = 2_000

BBox = tuple[float, float, float, float]


def _is_white(color: Any) -> bool:
    """Interpreta a cor de preenchimento do pdfminer (Gray, RGB ou CMYK)."""
    if color is None or isinstance(color, str):
        return False
    if isinstance(color, int | float):
        color = (color,)
    try:
        values = [float(c) for c in color]
    except (TypeError, ValueError):
        return False
    if len(values) == 1:
        return values[0] >= WHITE_THRESHOLD
    if len(values) == 3:
        return all(v >= WHITE_THRESHOLD for v in values)
    if len(values) == 4:
        return all(v <= 1 - WHITE_THRESHOLD for v in values)
    return False


def _union(boxes: Iterable[BBox]) -> BBox:
    boxes = list(boxes)
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _classify_word(word: dict[str, Any], width: float, height: float) -> str | None:
    x0, top, x1, bottom = word["x0"], word["top"], word["x1"], word["bottom"]
    m = OFF_PAGE_MARGIN
    if x1 < -m or x0 > width + m or bottom < -m or top > height + m:
        return "OFF_PAGE_TEXT"
    if float(word.get("size") or 0) < TINY_FONT_PT:
        return "TINY_FONT"
    # TODO: comparar com a cor real do fundo renderizado (hoje assume fundo branco).
    if _is_white(word.get("non_stroking_color")):
        return "WHITE_TEXT"
    return None


def _group_lines(words: list[dict[str, Any]], tol: float = 2.0) -> list[list[dict[str, Any]]]:
    lines: list[list[dict[str, Any]]] = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if lines and abs(lines[-1][-1]["top"] - w["top"]) <= tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    return lines


def _scan_layout(pdf: pdfplumber.PDF, out: ExtractionResult) -> None:
    for pno, page in enumerate(pdf.pages[:MAX_PAGES], start=1):
        width, height = float(page.width), float(page.height)
        words = page.extract_words(
            extra_attrs=["size", "non_stroking_color"], keep_blank_chars=False, use_text_flow=True
        )
        visible: list[str] = []
        flagged: dict[str, list[dict[str, Any]]] = {}
        for w in words:
            code = _classify_word(w, width, height)
            if code:
                flagged.setdefault(code, []).append(w)
            else:
                visible.append(w["text"])
        if visible:
            out.segments.append(TextSegment(" ".join(visible), page=pno))

        for code, ws in flagged.items():
            r = rule(code)
            for line in _group_lines(ws):
                text = " ".join(w["text"] for w in line)
                bbox = _union((w["x0"], w["top"], w["x1"], w["bottom"]) for w in line)
                out.findings.append(
                    Finding(
                        rule=r.code,
                        severity=r.severity,
                        page=pno,
                        bbox=bbox,
                        text=text[:500],
                        technique=r.technique,
                        detector_version=VERSION,
                        evidence={
                            "font_size": min(float(w.get("size") or 0) for w in line),
                            "color": str(line[0].get("non_stroking_color")),
                        },
                    )
                )
                out.segments.append(
                    TextSegment(text, page=pno, hidden=True, bbox=bbox, source=code.lower())
                )


def _decode_pdf_string(obj: Any) -> str:
    if isinstance(obj, pikepdf.String):
        raw = bytes(obj)
        # Melhor esforço: fontes simples usam encodings próximos de Latin-1.
        # TODO: usar o ToUnicode da fonte para fontes compostas (Identity-H).
        try:
            return (
                raw.decode("utf-16")
                if raw[:2] in (b"\xfe\xff", b"\xff\xfe")
                else raw.decode("latin-1")
            )
        except UnicodeDecodeError:
            return ""
    if isinstance(obj, pikepdf.Array):
        return "".join(_decode_pdf_string(o) for o in obj if isinstance(o, pikepdf.String))
    return ""


def _transparent_gstates(page: pikepdf.Page) -> set[str]:
    names: set[str] = set()
    resources = page.obj.get("/Resources") or {}
    ext = resources.get("/ExtGState") if isinstance(resources, pikepdf.Dictionary) else None
    if isinstance(ext, pikepdf.Dictionary):
        for name, gs in ext.items():
            if not isinstance(gs, pikepdf.Dictionary):
                continue
            ca = gs.get("/ca")
            if ca is not None and float(ca) == 0:
                names.add(str(name))
    return names


def _scan_content_streams(pdf: pikepdf.Pdf, out: ExtractionResult) -> None:
    """Texto com render mode 3 (invisível) ou desenhado com opacidade de preenchimento 0."""
    r = rule("TRANSPARENT_TEXT")
    for pno, page in enumerate(pdf.pages[:MAX_PAGES], start=1):
        zero_alpha = _transparent_gstates(page)
        try:
            instructions = pikepdf.parse_content_stream(page)
        except pikepdf.PdfError:
            continue
        stack: list[tuple[int, bool]] = []
        render_mode, transparent = 0, False
        hidden: dict[str, list[str]] = {"render_mode_3": [], "opacity_0": []}
        for operands, operator in instructions:
            op = str(operator)
            if op == "q":
                stack.append((render_mode, transparent))
            elif op == "Q" and stack:
                render_mode, transparent = stack.pop()
            elif op == "Tr" and operands:
                render_mode = int(operands[0])
            elif op == "gs" and operands:
                transparent = str(operands[0]) in zero_alpha
            elif op in ("Tj", "TJ", "'", '"') and operands:
                text = _decode_pdf_string(operands[-1])
                if not text.strip():
                    continue
                if render_mode == 3:
                    hidden["render_mode_3"].append(text)
                elif transparent:
                    hidden["opacity_0"].append(text)
        for reason, texts in hidden.items():
            if not texts:
                continue
            joined = " ".join(texts)
            out.findings.append(
                Finding(
                    rule=r.code,
                    severity=r.severity,
                    page=pno,
                    text=joined[:500],
                    technique=r.technique,
                    detector_version=VERSION,
                    evidence={"reason": reason, "operations": len(texts)},
                )
            )
            out.segments.append(TextSegment(joined, page=pno, hidden=True, source=reason))
            _remove_from_visible(out, pno, texts)


def _remove_from_visible(out: ExtractionResult, page: int, texts: list[str]) -> None:
    """O pdfplumber não expõe o render mode: tira do texto visível o que já sabemos ser oculto."""
    for seg in out.segments:
        if seg.page == page and not seg.hidden:
            for t in texts:
                seg.text = seg.text.replace(t.strip(), " ")


def extract(data: bytes) -> ExtractionResult:
    out = ExtractionResult()
    with pdfplumber.open(io.BytesIO(data)) as doc:
        out.page_count = len(doc.pages)
        _scan_layout(doc, out)
    with pikepdf.open(io.BytesIO(data)) as doc:
        _scan_content_streams(doc, out)
        out.extend(metadata.scan(doc))
    return out
