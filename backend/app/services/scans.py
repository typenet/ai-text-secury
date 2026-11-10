"""Executa um scan persistido: baixa o arquivo, roda o engine e grava findings e score."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Document, FindingRow, Scan, ScanStatus
from app.scanner import scan_bytes
from app.services.storage import Storage

log = logging.getLogger(__name__)


def run_scan(db: Session, storage: Storage, scan_id: uuid.UUID) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise LookupError(f"scan {scan_id} não encontrado")
    doc: Document = scan.document
    scan.status = ScanStatus.RUNNING
    scan.started_at = datetime.now(UTC)
    db.commit()
    try:
        report = scan_bytes(storage.get(doc.storage_key), doc.filename)
        scan.findings = [
            FindingRow(
                rule=f.rule,
                severity=f.severity.value,
                technique=f.technique,
                page=f.page,
                bbox=list(f.bbox) if f.bbox else None,
                text=f.text,
                confidence=f.confidence,
                detector_version=f.detector_version,
                evidence=f.evidence,
            )
            for f in report.findings
        ]
        scan.score = report.score
        scan.band = report.band.value
        scan.engine_version = report.engine_version
        scan.summary = report.summary
        doc.page_count = report.page_count
        scan.status = ScanStatus.DONE
    except Exception as exc:  # o erro fica registrado no scan, sem derrubar o worker
        log.exception("scan %s falhou", scan_id)
        db.rollback()
        scan = db.get(Scan, scan_id)
        scan.status = ScanStatus.FAILED
        scan.error = f"{type(exc).__name__}: {exc}"[:2000]
    scan.finished_at = datetime.now(UTC)
    db.commit()
    return scan
