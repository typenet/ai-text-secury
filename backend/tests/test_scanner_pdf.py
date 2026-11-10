from app.scanner import scan_bytes
from tests.fixtures import make_pdf


def rules_of(report):
    return {f.rule for f in report.findings}


def test_clean_pdf_is_safe():
    report = scan_bytes(make_pdf())
    assert report.findings == []
    assert report.score == 0
    assert report.band == "safe"


def test_white_text_with_injection_is_critical():
    report = scan_bytes(make_pdf(white=True))
    assert {"WHITE_TEXT", "PROMPT_INJECTION"} <= rules_of(report)
    inj = next(f for f in report.findings if f.rule == "PROMPT_INJECTION")
    assert inj.severity == "CRITICAL"
    assert report.band == "critical"


def test_tiny_font():
    assert "TINY_FONT" in rules_of(scan_bytes(make_pdf(tiny=True)))


def test_render_mode_3():
    report = scan_bytes(make_pdf(invisible=True))
    assert "TRANSPARENT_TEXT" in rules_of(report)
    # O texto oculto não deve gerar também um finding "visível".
    sev = [f.severity for f in report.findings if f.rule == "PROMPT_INJECTION"]
    assert sev == ["CRITICAL"]


def test_off_page():
    assert "OFF_PAGE_TEXT" in rules_of(scan_bytes(make_pdf(off_page=True)))


def test_javascript_open_action():
    rules = rules_of(scan_bytes(make_pdf(javascript=True)))
    assert {"EMBEDDED_JAVASCRIPT", "OPEN_ACTION"} <= rules


def test_finding_has_bbox():
    report = scan_bytes(make_pdf(white=True))
    white = next(f for f in report.findings if f.rule == "WHITE_TEXT")
    assert white.page == 1 and white.bbox is not None
