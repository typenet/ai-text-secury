"""Detecção de dados pessoais (LGPD). Beta: previsto para a v2, aqui só o básico com validação."""

from __future__ import annotations

import re

from app.scanner.findings import Finding, TextSegment
from app.scanner.rules import rule

VERSION = "lgpd@0.1.0"

_CPF = re.compile(r"(?<!\d)(\d{3}\.?\d{3}\.?\d{3}-?\d{2})(?!\d)")
_CNPJ = re.compile(r"(?<!\d)(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _digits(s: str) -> list[int]:
    return [int(c) for c in s if c.isdigit()]


def is_valid_cpf(value: str) -> bool:
    d = _digits(value)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        total = sum(d[i] * (n + 1 - i) for i in range(n))
        if (total * 10 % 11) % 10 != d[n]:
            return False
    return True


def is_valid_cnpj(value: str) -> bool:
    d = _digits(value)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, *w1]
    for weights, pos in ((w1, 12), (w2, 13)):
        r = sum(a * b for a, b in zip(d[:pos], weights, strict=True)) % 11
        if (0 if r < 2 else 11 - r) != d[pos]:
            return False
    return True


def mask(value: str) -> str:
    """Nunca persistir o dado completo no finding."""
    return value[:3] + "*" * max(len(value) - 5, 0) + value[-2:]


def scan_segments(segments: list[TextSegment]) -> list[Finding]:
    r = rule("SENSITIVE_DATA")
    counts: dict[str, list[str]] = {"cpf": [], "cnpj": [], "email": []}
    pages: set[int] = set()
    for seg in segments:
        found = (
            [("cpf", m) for m in _CPF.findall(seg.text) if is_valid_cpf(m)]
            + [("cnpj", m) for m in _CNPJ.findall(seg.text) if is_valid_cnpj(m)]
            + [("email", m) for m in _EMAIL.findall(seg.text)]
        )
        for kind, value in found:
            counts[kind].append(mask(value))
            if seg.page is not None:
                pages.add(seg.page)
    total = sum(len(v) for v in counts.values())
    if not total:
        return []
    return [
        Finding(
            rule=r.code,
            severity=r.severity,
            text=f"{total} dado(s) pessoal(is) encontrado(s)",
            confidence=90,
            technique=r.technique,
            detector_version=VERSION,
            evidence={
                "counts": {k: len(v) for k, v in counts.items() if v},
                "samples": {k: v[:5] for k, v in counts.items() if v},
                "pages": sorted(pages),
            },
        )
    ]
