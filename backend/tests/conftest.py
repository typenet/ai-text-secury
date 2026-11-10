import os

os.environ.setdefault("SCAN_EAGER", "true")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import generate_api_key  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ApiKey, Organization  # noqa: E402
from app.services.storage import MemoryStorage, get_storage  # noqa: E402


@pytest.fixture
def client():
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    storage = MemoryStorage()

    with Session() as db:
        org = Organization(name="Teste")
        db.add(org)
        db.flush()
        key, prefix, key_hash = generate_api_key()
        db.add(ApiKey(organization_id=org.id, name="t", prefix=prefix, key_hash=key_hash))
        db.commit()

    def _db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_storage] = lambda: storage
    with TestClient(app) as c:
        c.headers["X-API-Key"] = key
        yield c
    app.dependency_overrides.clear()
