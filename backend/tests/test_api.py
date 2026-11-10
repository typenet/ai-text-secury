from tests.fixtures import make_pdf


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_requires_api_key(client):
    r = client.get("/v1/scans/00000000-0000-0000-0000-000000000000", headers={"X-API-Key": ""})
    assert r.status_code == 401


def test_scan_flow(client):
    pdf = make_pdf(white=True)
    r = client.post("/v1/scans", files={"file": ("cv.pdf", pdf, "application/pdf")})
    assert r.status_code == 202, r.text
    scan_id = r.json()["id"]

    body = client.get(f"/v1/scans/{scan_id}").json()
    assert body["status"] == "done"
    assert body["band"] == "critical"
    assert body["document"]["doc_type"] == "pdf"
    assert any(f["rule"] == "WHITE_TEXT" for f in body["findings"])


def test_rejects_unsupported(client):
    r = client.post("/v1/scans", files={"file": ("x.bin", b"\x00\x01\x02binario", "application/x")})
    assert r.status_code == 415
