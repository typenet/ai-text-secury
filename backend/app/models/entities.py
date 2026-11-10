"""Modelo de dados multi-tenant.

organizations -> users, projects, api_keys
projects -> documents -> scans -> findings / reports
Um documento pode ser reanalisado (novo scan) quando as regras mudam, sem perder histórico.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType


def _now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    retention_days: Mapped[int] = mapped_column(Integer, default=30)

    users: Mapped[list[User]] = relationship(back_populates="organization")
    projects: Mapped[list[Project]] = relationship(back_populates="organization")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="member")  # owner, admin, member

    organization: Mapped[Organization] = relationship(back_populates="users")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    settings: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    organization: Mapped[Organization] = relationship(back_populates="projects")


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(100))
    prefix: Mapped[str] = mapped_column(String(16))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), index=True)
    filename: Mapped[str] = mapped_column(String(500))
    doc_type: Mapped[str] = mapped_column(String(10))  # pdf, docx, txt
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_key: Mapped[str] = mapped_column(String(500))
    page_count: Mapped[int | None] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    scans: Mapped[list[Scan]] = relationship(back_populates="document")
    pages: Mapped[list[DocumentPage]] = relationship(back_populates="document")


class DocumentPage(Base):
    __tablename__ = "document_pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    width: Mapped[float | None] = mapped_column(Float)
    height: Mapped[float | None] = mapped_column(Float)

    document: Mapped[Document] = relationship(back_populates="pages")


class ScanStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Scan(TimestampMixin, Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status", values_callable=lambda e: [m.value for m in e]),
        default=ScanStatus.QUEUED,
        index=True,
    )
    score: Mapped[int | None] = mapped_column(Integer)
    band: Mapped[str | None] = mapped_column(String(20))
    engine_version: Mapped[str | None] = mapped_column(String(20))
    summary: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    document: Mapped[Document] = relationship(back_populates="scans")
    findings: Mapped[list[FindingRow]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )


class FindingRow(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id"), index=True)
    rule: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(10))
    technique: Mapped[str] = mapped_column(String(30))
    page: Mapped[int | None] = mapped_column(Integer)
    bbox: Mapped[list[float] | None] = mapped_column(JSONType)
    text: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[int] = mapped_column(Integer)
    detector_version: Mapped[str] = mapped_column(String(40))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    scan: Mapped[Scan] = relationship(back_populates="findings")


class RuleRow(Base):
    __tablename__ = "rules"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    severity: Mapped[str] = mapped_column(String(10))
    technique: Mapped[str] = mapped_column(String(30))
    formats: Mapped[list[str]] = mapped_column(JSONType)
    description: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(default=True)


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id"), index=True)
    format: Mapped[str] = mapped_column(String(10))  # json, pdf
    storage_key: Mapped[str] = mapped_column(String(500))
