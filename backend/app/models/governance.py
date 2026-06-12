import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, utcnow, uuid_pk
from app.models.org import JSONType


class ComplianceTask(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "compliance_tasks"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True, nullable=False)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    area: Mapped[str] = mapped_column(String(20), nullable=False)  # fiscal|contabil|financeiro|juridico|ti|vendas|compras
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(15), default="pendente", nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="media", nullable=False)  # baixa|media|alta
    due_date: Mapped[date | None] = mapped_column(Date)
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    legal_update_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("legal_updates.id"))


class LegalUpdate(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "legal_updates"

    id: Mapped[uuid.UUID] = uuid_pk()
    norm_type: Mapped[str] = mapped_column(String(20), nullable=False)  # lei|lc|decreto|nota_tecnica|portaria|outro
    reference: Mapped[str] = mapped_column(String(120), nullable=False)  # ex.: 'LC 214/2025'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(String(10), default="medio", nullable=False)  # baixo|medio|alto|critico
    source_url: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[date | None] = mapped_column(Date)


class Report(Base, TimestampMixin, TenantMixin):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    simulation_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("simulations.id"))
    generated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    report_type: Mapped[str] = mapped_column(String(40), nullable=False)  # impacto_executivo|itens|...
    format: Mapped[str] = mapped_column(String(8), nullable=False)  # pdf|xlsx|csv
    file_path: Mapped[str | None] = mapped_column(String(500))
    premises: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)  # premissas declaradas


class AIConversation(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    messages: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    model: Mapped[str | None] = mapped_column(String(60))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base, TenantMixin):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_org_created", "organization_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(60), index=True, nullable=False)  # ex.: company.create
    entity_type: Mapped[str | None] = mapped_column(String(60), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(40))
    extra: Mapped[dict] = mapped_column("metadata", JSONType, default=dict, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
