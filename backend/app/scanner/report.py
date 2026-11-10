"""Score de risco (0-100) e relatório.

score = 100 * (1 - prod(1 - w_i * c_i)), com w = peso da severidade e c = confiança (0..1).
A combinação satura: dez achados baixos não superam um crítico.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.scanner.findings import SEVERITY_WEIGHT, Finding, Severity

HIDDEN_TECHNIQUES = {"hidden_text", "unicode"}


class RiskBand(StrEnum):
    SAFE = "safe"  # 0-20
    ATTENTION = "attention"  # 21-50
    HIGH = "high"  # 51-80
    CRITICAL = "critical"  # 81-100


def band_for(score: int) -> RiskBand:
    if score <= 20:
        return RiskBand.SAFE
    if score <= 50:
        return RiskBand.ATTENTION
    if score <= 80:
        return RiskBand.HIGH
    return RiskBand.CRITICAL


def compute_score(findings: list[Finding]) -> int:
    remaining = 1.0
    for f in findings:
        w = SEVERITY_WEIGHT[f.severity]
        c = max(0, min(f.confidence, 100)) / 100
        remaining *= 1 - w * c
    score = round(100 * (1 - remaining))
    # Texto oculto + prompt injection leva direto para crítico.
    has_hidden = any(f.technique in HIDDEN_TECHNIQUES for f in findings)
    has_injection = any(f.rule == "PROMPT_INJECTION" for f in findings)
    if has_hidden and has_injection:
        score = max(score, 90)
    return min(score, 100)


@dataclass(slots=True)
class ScanReport:
    score: int
    band: RiskBand
    findings: list[Finding]
    page_count: int
    engine_version: str
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "band": self.band.value,
            "page_count": self.page_count,
            "engine_version": self.engine_version,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
        }


def build_report(findings: list[Finding], page_count: int, engine_version: str) -> ScanReport:
    order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
    findings = sorted(findings, key=lambda f: (order[f.severity], f.page or 0))
    score = compute_score(findings)
    summary = {
        "by_severity": dict(Counter(f.severity.value for f in findings)),
        "by_rule": dict(Counter(f.rule for f in findings)),
    }
    return ScanReport(score, band_for(score), findings, page_count, engine_version, summary)
