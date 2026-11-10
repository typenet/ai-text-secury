"""Tipos centrais do scanner: severidade, finding e segmentos de texto."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Peso usado no cálculo do score (ver report.py).
SEVERITY_WEIGHT: dict[Severity, float] = {
    Severity.LOW: 0.1,
    Severity.MEDIUM: 0.3,
    Severity.HIGH: 0.6,
    Severity.CRITICAL: 0.9,
}


@dataclass(slots=True)
class Finding:
    """Um achado de um detector.

    `confidence` vai de 0 a 100. `bbox` usa coordenadas da página em pontos
    (x0, top, x1, bottom), no mesmo sistema do pdfplumber, para destacar no viewer.
    """

    rule: str
    severity: Severity
    text: str = ""
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    confidence: int = 100
    technique: str = "hidden_text"
    detector_version: str = "0.1.0"
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["bbox"] = list(self.bbox) if self.bbox else None
        return data


@dataclass(slots=True)
class TextSegment:
    """Trecho de texto extraído. `hidden=True` quando veio de um detector de ocultação."""

    text: str
    page: int | None = None
    hidden: bool = False
    source: str = "body"  # body, metadata, comment, form_field, ...
    bbox: tuple[float, float, float, float] | None = None


@dataclass(slots=True)
class ExtractionResult:
    """Saída de um extrator de formato (pdf, docx, txt)."""

    findings: list[Finding] = field(default_factory=list)
    segments: list[TextSegment] = field(default_factory=list)
    page_count: int = 1

    def extend(self, other: ExtractionResult) -> None:
        self.findings.extend(other.findings)
        self.segments.extend(other.segments)
