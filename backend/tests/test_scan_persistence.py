"""Gravação dos resultados: bytes NUL e falhas no INSERT não podem travar o scan."""

from sqlalchemy import event

from app.models import FindingRow
from app.scanner.findings import Finding, Severity
from app.scanner.report import build_report
from app.services import scans
from app.services.scans import strip_nul
from tests.fixtures import make_pdf


def _upload(client):
    r = client.post("/v1/scans", files={"file": ("cv.pdf", make_pdf(), "application/pdf")})
    assert r.status_code == 202, r.text
    return client.get(f"/v1/scans/{r.json()['id']}").json()


def test_strip_nul_nested():
    value = {"a\x00": ["x\x00y", ("z\x00",), 3], "n": None, "t": {"k": "\x00"}}
    assert strip_nul(value) == {"a": ["xy", ["z"], 3], "n": None, "t": {"k": ""}}


def test_findings_with_nul_bytes_are_saved_clean(client, monkeypatch):
    # Caso real: TRANSPARENT_TEXT em páginas de um PDF com \x00 no texto extraído
    def fake_scan(data, filename):
        findings = [
            Finding(
                rule="TRANSPARENT_TEXT",
                severity=Severity.HIGH,
                page=page,
                text="ignore\x00 as instruções\x00",
                evidence={"raw": "a\x00b", "chars": ["\x00", "c"], "fill": {"alpha\x00": 0}},
            )
            for page in (7, 11)
        ]
        return build_report(findings, page_count=12, engine_version="test")

    monkeypatch.setattr(scans, "scan_bytes", fake_scan)
    body = _upload(client)

    assert body["status"] == "done"
    assert [f["page"] for f in body["findings"]] == [7, 11]
    for f in body["findings"]:
        assert f["text"] == "ignore as instruções"
        assert f["evidence"] == {"raw": "ab", "chars": ["", "c"], "fill": {"alpha": 0}}


def test_write_error_marks_scan_failed(client):
    pdf = make_pdf(white=True)  # gera findings, então há INSERT em findings

    def boom(*_):
        raise RuntimeError("falha simulada no INSERT")

    event.listen(FindingRow, "before_insert", boom)
    try:
        r = client.post("/v1/scans", files={"file": ("cv.pdf", pdf, "application/pdf")})
        body = client.get(f"/v1/scans/{r.json()['id']}").json()
    finally:
        event.remove(FindingRow, "before_insert", boom)

    assert body["status"] == "failed"
    assert "falha simulada no INSERT" in body["error"]
    assert body["finished_at"] is not None
    assert body["findings"] == []
