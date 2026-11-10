from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule: str
    severity: str
    technique: str
    page: int | None
    bbox: list[float] | None
    text: str
    confidence: int
    detector_version: str
    evidence: dict[str, Any]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    doc_type: str
    size_bytes: int
    sha256: str
    page_count: int | None


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    score: int | None
    band: str | None
    engine_version: str | None
    summary: dict[str, Any]
    error: str | None
    created_at: datetime
    finished_at: datetime | None
    document: DocumentOut
    findings: list[FindingOut] = []
