import uuid

from app.db.session import SessionLocal
from app.services.scans import run_scan
from app.services.storage import get_storage
from app.worker.celery_app import celery_app


@celery_app.task(name="scans.run")
def run_scan_task(scan_id: str) -> str:
    with SessionLocal() as db:
        scan = run_scan(db, get_storage(), uuid.UUID(scan_id))
        return scan.status.value
