import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentKey, DbSession, StorageDep
from app.core.config import get_settings
from app.models import Document, Scan
from app.scanner.engine import UnsupportedDocument, detect_type
from app.schemas.scan import ScanOut
from app.services.scans import run_scan

router = APIRouter(prefix="/v1/scans", tags=["scans"])

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


@router.post("", response_model=ScanOut, status_code=status.HTTP_202_ACCEPTED)
def create_scan(
    db: DbSession, storage: StorageDep, api_key: CurrentKey, file: Annotated[UploadFile, File()]
) -> Scan:
    """Envia um documento (PDF, DOCX ou TXT) para análise. O resultado sai em GET /v1/scans/{id}."""
    settings = get_settings()
    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "arquivo grande demais")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "arquivo vazio")
    try:
        doc_type = detect_type(data, file.filename)
    except UnsupportedDocument as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc

    sha = hashlib.sha256(data).hexdigest()
    doc_id = uuid.uuid4()
    key = f"{api_key.organization_id}/{doc_id}/{sha}.{doc_type.value}"
    storage.put(key, data, CONTENT_TYPES[doc_type.value])

    doc = Document(
        id=doc_id,
        organization_id=api_key.organization_id,
        project_id=api_key.project_id,
        filename=(file.filename or "documento")[:500],
        doc_type=doc_type.value,
        size_bytes=len(data),
        sha256=sha,
        storage_key=key,
    )
    scan = Scan(organization_id=api_key.organization_id, document=doc)
    db.add_all([doc, scan])
    db.commit()

    if settings.scan_eager:
        run_scan(db, storage, scan.id)
    else:
        from app.worker.tasks import run_scan_task

        run_scan_task.delay(str(scan.id))
    db.refresh(scan)
    return scan


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: uuid.UUID, db: DbSession, api_key: CurrentKey) -> Scan:
    scan = db.get(Scan, scan_id, options=[selectinload(Scan.findings), selectinload(Scan.document)])
    if scan is None or scan.organization_id != api_key.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "scan não encontrado")
    return scan
