import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import cli
from app.core.config import get_settings
from app.core.security import hash_api_key
from app.db import session as db_session
from app.db.base import Base
from app.models import ApiKey, Organization


@pytest.fixture
def db(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(db_session, "SessionLocal", Session)
    yield Session
    get_settings.cache_clear()


def _count(Session, model):
    with Session() as s:
        return s.scalar(select(func.count()).select_from(model))


def test_seed_with_fixed_key_is_idempotent(db, monkeypatch, capsys):
    key = "ats_chave_fixa_de_teste_123456"
    monkeypatch.setenv("BOOTSTRAP_API_KEY", key)
    get_settings.cache_clear()

    cli.seed()
    cli.seed()

    assert _count(db, ApiKey) == 1
    assert _count(db, Organization) == 1
    with db() as s:
        assert s.scalar(select(ApiKey).where(ApiKey.key_hash == hash_api_key(key)))
    assert "já cadastrada" in capsys.readouterr().out


def test_seed_generates_key_only_once(db, monkeypatch, capsys):
    monkeypatch.delenv("BOOTSTRAP_API_KEY", raising=False)
    get_settings.cache_clear()

    cli.seed()
    first = capsys.readouterr().out
    cli.seed()

    assert "API key gerada" in first
    assert _count(db, ApiKey) == 1


def test_seed_rejects_bad_key(db, monkeypatch):
    monkeypatch.setenv("BOOTSTRAP_API_KEY", "curta")
    get_settings.cache_clear()
    with pytest.raises(SystemExit):
        cli.seed()


def test_ready_reports_each_dependency(client, monkeypatch):
    from app.worker.celery_app import celery_app

    class Conn:
        def ensure_connection(self, **_):
            raise ConnectionError("redis fora")

    monkeypatch.setattr(celery_app, "connection_for_write", lambda: Conn())
    r = client.get("/health/ready")
    assert r.status_code == 503
    assert r.json()["checks"] == {"database": "ok", "redis": "error", "storage": "ok"}
