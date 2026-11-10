"""Catálogo das regras iniciais. A tabela `rules` do banco é populada a partir daqui."""

from __future__ import annotations

from dataclasses import dataclass

from app.scanner.findings import Severity


@dataclass(frozen=True, slots=True)
class Rule:
    code: str
    formats: tuple[str, ...]
    severity: Severity
    technique: str
    description: str


RULES: dict[str, Rule] = {
    r.code: r
    for r in [
        Rule(
            "WHITE_TEXT",
            ("pdf", "docx"),
            Severity.HIGH,
            "hidden_text",
            "Texto da mesma cor do fundo (ex.: branco no branco).",
        ),
        Rule("TINY_FONT", ("pdf", "docx"), Severity.MEDIUM, "hidden_text", "Fonte menor que 2 pt."),
        Rule(
            "TRANSPARENT_TEXT",
            ("pdf",),
            Severity.HIGH,
            "hidden_text",
            "Texto invisível: render mode 3 ou opacidade 0.",
        ),
        Rule(
            "OFF_PAGE_TEXT",
            ("pdf",),
            Severity.HIGH,
            "hidden_text",
            "Texto posicionado fora da área visível da página.",
        ),
        Rule(
            "HIDDEN_LAYER",
            ("pdf",),
            Severity.HIGH,
            "hidden_text",
            "Camada opcional (OCG) desligada por padrão.",
        ),
        Rule(
            "TEXT_UNDER_IMAGE",
            ("pdf",),
            Severity.MEDIUM,
            "hidden_text",
            "Texto coberto por imagem ou objeto (confirmado via render/OCR).",
        ),
        Rule(
            "HIDDEN_DOCX_TEXT",
            ("docx",),
            Severity.HIGH,
            "hidden_text",
            "Texto marcado como oculto no Word (w:vanish / w:webHidden).",
        ),
        Rule(
            "INVISIBLE_UNICODE",
            ("pdf", "docx", "txt"),
            Severity.MEDIUM,
            "unicode",
            "Caracteres invisíveis: zero-width, tag characters (U+E0000).",
        ),
        Rule(
            "BIDI_CONTROL",
            ("pdf", "docx", "txt"),
            Severity.MEDIUM,
            "unicode",
            "Controles de direção bidi (U+202A..U+202E, U+2066..U+2069).",
        ),
        Rule(
            "HIDDEN_COMMENT",
            ("pdf", "docx"),
            Severity.LOW,
            "container",
            "Comentários ou anotações ocultas.",
        ),
        Rule(
            "HIDDEN_FORM_FIELD",
            ("pdf", "docx"),
            Severity.MEDIUM,
            "container",
            "Campo de formulário marcado como oculto.",
        ),
        Rule(
            "SUSPICIOUS_METADATA",
            ("pdf", "docx"),
            Severity.LOW,
            "container",
            "Metadados longos ou com cara de instrução.",
        ),
        Rule(
            "EMBEDDED_JAVASCRIPT",
            ("pdf",),
            Severity.HIGH,
            "active_content",
            "JavaScript embutido (/JS, /JavaScript).",
        ),
        Rule(
            "OPEN_ACTION",
            ("pdf",),
            Severity.MEDIUM,
            "active_content",
            "Ação automática ao abrir (/OpenAction, /AA).",
        ),
        Rule(
            "EMBEDDED_FILE",
            ("pdf", "docx"),
            Severity.MEDIUM,
            "active_content",
            "Arquivo ou objeto OLE embutido.",
        ),
        Rule(
            "PROMPT_INJECTION",
            ("pdf", "docx", "txt"),
            Severity.CRITICAL,
            "prompt_injection",
            "Instrução direcionada a IA. Crítica quando o trecho também está oculto.",
        ),
        Rule(
            "SENSITIVE_DATA",
            ("pdf", "docx", "txt"),
            Severity.MEDIUM,
            "lgpd",
            "Dados pessoais (CPF, CNPJ, e-mail, telefone). Beta, previsto para a v2.",
        ),
    ]
}


def rule(code: str) -> Rule:
    return RULES[code]
