from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_api_key
from app.db.session import get_db
from app.models import ApiKey
from app.services.storage import Storage, get_storage

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
StorageDep = Annotated[Storage, Depends(get_storage)]


def get_api_key(db: DbSession, key: str | None = Security(api_key_header)) -> ApiKey:
    if not key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-API-Key ausente")
    api_key = db.scalar(
        select(ApiKey).where(ApiKey.key_hash == hash_api_key(key), ApiKey.revoked_at.is_(None))
    )
    if api_key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key inválida")
    api_key.last_used_at = datetime.now(UTC)
    db.commit()
    return api_key


CurrentKey = Annotated[ApiKey, Depends(get_api_key)]
