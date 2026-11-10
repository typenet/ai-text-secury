"""Detecção de Unicode invisível e controles bidi. Roda sobre o texto de todos os formatos."""

from __future__ import annotations

from app.scanner.findings import Finding, TextSegment
from app.scanner.rules import rule

VERSION = "unicode@0.1.0"

ZERO_WIDTH = {
    "​",  # ZERO WIDTH SPACE
    "‌",  # ZERO WIDTH NON-JOINER
    "‍",  # ZERO WIDTH JOINER
    "⁠",  # WORD JOINER
    "⁡",
    "⁢",
    "⁣",
    "⁤",  # invisible math operators
    "﻿",  # BOM / ZWNBSP (fora do início do texto)
    "᠎",  # MONGOLIAN VOWEL SEPARATOR
    "­",  # SOFT HYPHEN
}
BIDI = {chr(c) for c in [*range(0x202A, 0x202F), *range(0x2066, 0x206A), 0x200E, 0x200F]}
TAG_RANGE = range(0xE0000, 0xE0080)


def decode_tags(text: str) -> str:
    """Decodifica tag characters (U+E0020..U+E007E) para ASCII, revelando o texto escondido."""
    return "".join(chr(ord(c) - 0xE0000) for c in text if 0xE0020 <= ord(c) <= 0xE007E)


def strip_invisible(text: str) -> str:
    return "".join(
        c for c in text if c not in ZERO_WIDTH and c not in BIDI and ord(c) not in TAG_RANGE
    )


def scan_segment(seg: TextSegment) -> tuple[list[Finding], TextSegment | None]:
    """Retorna findings e, se houver tag characters, um segmento oculto com o texto decodificado."""
    text = seg.text.lstrip("﻿")
    zw = [c for c in text if c in ZERO_WIDTH]
    bidi = [c for c in text if c in BIDI]
    tags = [c for c in text if ord(c) in TAG_RANGE]
    findings: list[Finding] = []
    hidden: TextSegment | None = None

    if zw or tags:
        r = rule("INVISIBLE_UNICODE")
        decoded = decode_tags(text) if tags else ""
        findings.append(
            Finding(
                rule=r.code,
                severity=r.severity,
                page=seg.page,
                text=decoded or strip_invisible(text)[:200],
                technique=r.technique,
                detector_version=VERSION,
                evidence={
                    "zero_width_count": len(zw),
                    "tag_char_count": len(tags),
                    "codepoints": sorted({f"U+{ord(c):04X}" for c in zw + tags})[:20],
                    "source": seg.source,
                },
            )
        )
        if decoded.strip():
            hidden = TextSegment(decoded, page=seg.page, hidden=True, source="unicode_tags")

    if bidi:
        r = rule("BIDI_CONTROL")
        findings.append(
            Finding(
                rule=r.code,
                severity=r.severity,
                page=seg.page,
                text=strip_invisible(text)[:200],
                technique=r.technique,
                detector_version=VERSION,
                evidence={
                    "count": len(bidi),
                    "codepoints": sorted({f"U+{ord(c):04X}" for c in bidi}),
                    "source": seg.source,
                },
            )
        )
    return findings, hidden
