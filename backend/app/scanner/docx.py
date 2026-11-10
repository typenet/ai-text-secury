"""Extrator + regras de DOCX. Lê o XML direto (lxml) para enxergar o que o python-docx esconde."""

from __future__ import annotations

import io
import zipfile

from lxml import etree

from app.scanner.findings import ExtractionResult, Finding, TextSegment
from app.scanner.rules import rule

VERSION = "docx@0.1.0"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {
    "w": W,
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
}
TEXT_PARTS = (
    "word/document.xml",
    "word/header",
    "word/footer",
    "word/footnotes.xml",
    "word/endnotes.xml",
)
WHITE = {"FFFFFF", "FFFFFE", "FEFEFE"}
TINY_HALF_POINTS = 4  # w:sz é em meio-ponto: < 4 => < 2 pt
META_SUSPICIOUS_LEN = 300
MAX_XML_BYTES = 50 * 1024 * 1024  # proteção contra zip bomb


def _parser() -> etree.XMLParser:
    # Sem resolução de entidades externas nem rede (XXE).
    return etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)


def _read_xml(z: zipfile.ZipFile, name: str) -> etree._Element | None:
    try:
        info = z.getinfo(name)
    except KeyError:
        return None
    if info.file_size > MAX_XML_BYTES:
        raise ValueError(f"parte {name} grande demais")
    return etree.fromstring(z.read(name), _parser())


def _run_props(run: etree._Element) -> dict[str, str | bool | None]:
    rpr = run.find("w:rPr", NS)
    props: dict[str, str | bool | None] = {
        "vanish": False,
        "color": None,
        "sz": None,
        "highlight": None,
    }
    if rpr is None:
        return props
    for tag in ("vanish", "webHidden", "specVanish"):
        el = rpr.find(f"w:{tag}", NS)
        if el is not None and el.get(f"{{{W}}}val", "true") not in ("0", "false"):
            props["vanish"] = True
    color = rpr.find("w:color", NS)
    if color is not None:
        props["color"] = (color.get(f"{{{W}}}val") or "").upper()
    sz = rpr.find("w:sz", NS)
    if sz is not None:
        props["sz"] = sz.get(f"{{{W}}}val")
    hl = rpr.find("w:highlight", NS)
    if hl is not None:
        props["highlight"] = hl.get(f"{{{W}}}val")
    return props


def _scan_body(root: etree._Element, part: str, out: ExtractionResult) -> None:
    hidden_by_rule: dict[str, list[str]] = {}
    for para in root.iter(f"{{{W}}}p"):
        visible: list[str] = []
        for run in para.iter(f"{{{W}}}r"):
            text = "".join(t.text or "" for t in run.iter(f"{{{W}}}t"))
            if not text:
                continue
            p = _run_props(run)
            flagged = None
            if p["vanish"]:
                flagged = "HIDDEN_DOCX_TEXT"
            elif p["color"] in WHITE and not p["highlight"]:
                # TODO: considerar sombreamento de parágrafo/célula e cor de fundo da página.
                flagged = "WHITE_TEXT"
            elif p["sz"] and str(p["sz"]).isdigit() and int(str(p["sz"])) < TINY_HALF_POINTS:
                flagged = "TINY_FONT"
            if flagged:
                hidden_by_rule.setdefault(flagged, []).append(text)
            else:
                visible.append(text)
        if visible:
            out.segments.append(TextSegment("".join(visible), page=None, source=part))

    for code, texts in hidden_by_rule.items():
        r = rule(code)
        joined = " ".join(texts)
        out.findings.append(
            Finding(
                rule=r.code,
                severity=r.severity,
                text=joined[:500],
                technique=r.technique,
                detector_version=VERSION,
                evidence={"part": part, "runs": len(texts)},
            )
        )
        out.segments.append(TextSegment(joined, hidden=True, source=part))


def extract(data: bytes) -> ExtractionResult:
    out = ExtractionResult(page_count=1)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()

        for name in names:
            if name.startswith(TEXT_PARTS) and name.endswith(".xml"):
                root = _read_xml(z, name)
                if root is not None:
                    _scan_body(root, name, out)

        # Comentários
        comments = _read_xml(z, "word/comments.xml")
        if comments is not None:
            texts = ["".join(c.itertext()).strip() for c in comments.iter(f"{{{W}}}comment")]
            texts = [t for t in texts if t]
            if texts:
                r = rule("HIDDEN_COMMENT")
                out.findings.append(
                    Finding(
                        rule=r.code,
                        severity=r.severity,
                        text=" | ".join(texts)[:500],
                        technique=r.technique,
                        detector_version=VERSION,
                        evidence={"count": len(texts)},
                    )
                )
                out.segments.extend(TextSegment(t, hidden=True, source="comment") for t in texts)

        # Metadados (core.xml)
        core = _read_xml(z, "docProps/core.xml")
        if core is not None:
            for el in core:
                value = (el.text or "").strip()
                if not value:
                    continue
                out.segments.append(TextSegment(value, hidden=True, source="metadata"))
                if len(value) > META_SUSPICIOUS_LEN:
                    r = rule("SUSPICIOUS_METADATA")
                    out.findings.append(
                        Finding(
                            rule=r.code,
                            severity=r.severity,
                            text=value[:500],
                            technique=r.technique,
                            detector_version=VERSION,
                            evidence={"field": etree.QName(el).localname},
                        )
                    )

        # Objetos embutidos
        embedded = [n for n in names if n.startswith("word/embeddings/")]
        if embedded:
            r = rule("EMBEDDED_FILE")
            out.findings.append(
                Finding(
                    rule=r.code,
                    severity=r.severity,
                    text=", ".join(embedded)[:500],
                    technique=r.technique,
                    detector_version=VERSION,
                    evidence={"files": embedded[:20]},
                )
            )
    return out
