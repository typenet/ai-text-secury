"""Classificador de prompt injection.

Baseline heurístico (regex PT/EN) para o esqueleto. A interface `InjectionClassifier`
permite trocar por um modelo Transformers exportado para ONNX sem mudar o engine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from app.scanner.findings import Finding, Severity, TextSegment
from app.scanner.rules import rule

VERSION = "injection-heuristic@0.1.0"


@dataclass(slots=True)
class Prediction:
    is_injection: bool
    confidence: float  # 0..1
    matched: list[str]


class InjectionClassifier(Protocol):
    def predict(self, text: str) -> Prediction: ...


_PATTERNS: list[tuple[str, float]] = [
    # Inglês
    (r"ignore (all |any )?(the )?(previous|prior|above) (instructions|prompts?|rules)", 0.95),
    (r"disregard (all |the )?(previous|prior|above)", 0.9),
    (r"you are (now )?(a|an|the) [a-z ]{0,30}(assistant|ai|model|reviewer)", 0.6),
    (r"(system|developer) prompt", 0.6),
    (r"do not (mention|reveal|tell)", 0.6),
    (r"(give|assign) (a )?(positive|high|favorable) (review|score|rating)", 0.9),
    (r"recommend (this|the) (candidate|paper|applicant)", 0.85),
    (r"\b(as an? (ai|llm|language model))\b", 0.5),
    # Português
    (r"ignore (todas )?(as )?instru[cç][oõ]es (anteriores|acima|pr[eé]vias)", 0.95),
    (r"desconsidere (todas )?(as )?(instru[cç][oõ]es|regras)", 0.9),
    (r"voc[eê] (agora )?[eé] (um|uma) [a-zà-ú ]{0,30}(assistente|ia|modelo|avaliador)", 0.6),
    (r"n[aã]o (mencione|revele|conte)", 0.55),
    (
        r"(aprove|recomende|classifique) (este|esta|o|a) (candidato|candidata|contrato|documento)",
        0.85,
    ),
    (r"(d[eê]|atribua) (uma )?(nota|avalia[cç][aã]o) (m[aá]xima|alta|positiva)", 0.9),
    (r"prompt (do sistema|de sistema)", 0.6),
]
_COMPILED = [(re.compile(p, re.IGNORECASE), w) for p, w in _PATTERNS]


class HeuristicClassifier:
    def predict(self, text: str) -> Prediction:
        matched: list[str] = []
        score = 0.0
        for rx, weight in _COMPILED:
            m = rx.search(text)
            if m:
                matched.append(m.group(0))
                # Combinação que satura (mesma ideia do score do documento).
                score = 1 - (1 - score) * (1 - weight)
        return Prediction(is_injection=score >= 0.5, confidence=score, matched=matched)


_default: InjectionClassifier = HeuristicClassifier()


def set_classifier(clf: InjectionClassifier) -> None:
    global _default
    _default = clf


def scan_segments(segments: list[TextSegment]) -> list[Finding]:
    r = rule("PROMPT_INJECTION")
    findings: list[Finding] = []
    for seg in segments:
        if not seg.text.strip():
            continue
        pred = _default.predict(seg.text)
        if not pred.is_injection:
            continue
        # Visível: alta. Oculto: crítica (técnica de ocultação + instrução para IA).
        severity = Severity.CRITICAL if seg.hidden else Severity.HIGH
        findings.append(
            Finding(
                rule=r.code,
                severity=severity,
                page=seg.page,
                bbox=seg.bbox,
                text=seg.text[:500],
                confidence=round(pred.confidence * 100),
                technique=r.technique,
                detector_version=VERSION,
                evidence={"matched": pred.matched, "hidden": seg.hidden, "source": seg.source},
            )
        )
    return findings
