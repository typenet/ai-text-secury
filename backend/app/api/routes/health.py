import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.api.deps import DbSession, StorageDep

router = APIRouter(tags=["health"])
log = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: o processo está de pé."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: DbSession, storage: StorageDep, response: Response) -> dict[str, object]:
    """Readiness: banco, fila e storage respondendo. Usado pelo healthcheck do Docker."""
    from app.worker.celery_app import celery_app

    checks: dict[str, str] = {}

    def run(name: str, fn) -> None:
        try:
            fn()
            checks[name] = "ok"
        except Exception as exc:  # noqa: BLE001 - qualquer falha deixa o serviço não pronto
            log.warning("readiness %s falhou: %s", name, exc)
            checks[name] = "error"

    run("database", lambda: db.execute(text("SELECT 1")))
    run("redis", lambda: celery_app.connection_for_write().ensure_connection(max_retries=1))
    run("storage", lambda: getattr(storage, "ping", lambda: None)())

    ok = all(v == "ok" for v in checks.values())
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ok else "degraded", "checks": checks}
