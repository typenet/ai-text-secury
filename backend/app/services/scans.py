"""Executa um scan persistido: baixa o arquivo, roda o engine e grava findings e score."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Document, FindingRow, Scan, ScanStatus
from app.scanner import scan_bytes
from app.services.storage import Storage

log = logging.getLogger(__name__)


def strip_nul(value: Any) -> Any:
    """Remove bytes NUL (\\x00) de strings, inclusive dentro de dicts/listas.

    O Postgres recusa NUL em TEXT e em JSONB (mesmo escapado como \\u0000), e PDFs
    maliciosos ou malformados trazem esse byte no texto extraído.
    """
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, dict):
        return {strip_nul(k): strip_nul(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [strip_nul(v) for v in value]
    return value


def _mark_failed(db: Session, scan_id: uuid.UUID, exc: Exception) -> Scan:
    db.rollback()
    scan = db.get(Scan, scan_id)
    scan.status = ScanStatus.FAILED
    scan.error = strip_nul(f"{type(exc).__name__}: {exc}")[:2000]
    scan.finished_at = datetime.now(UTC)
    db.commit()
    return scan


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
                text=strip_nul(f.text),
                confidence=f.confidence,
                detector_version=f.detector_version,
                evidence=strip_nul(f.evidence),
            )
            for f in report.findings
        ]
        scan.score = report.score
        scan.band = report.band.value
        scan.engine_version = report.engine_version
        scan.summary = strip_nul(report.summary)
        doc.page_count = report.page_count
        scan.status = ScanStatus.DONE
        scan.finished_at = datetime.now(UTC)
        # O INSERT dos findings acontece aqui: o commit precisa estar dentro do try para
        # que um erro de gravação marque o scan como failed em vez de deixá-lo em running.
        db.commit()
    except Exception as exc:  # o erro fica registrado no scan, sem derrubar o worker
        log.exception("scan %s falhou", scan_id)
        return _mark_failed(db, scan_id, exc)
    return scan
