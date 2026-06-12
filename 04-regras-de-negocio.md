import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, uuid_pk

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(30), default="trial", nullable=False)
    # Premissas configuraveis do motor tributario (ver schemas.org.Assumptions)
    assumptions: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    lgpd_consent_version: Mapped[str | None] = mapped_column(String(20))
    lgpd_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    companies: Mapped[list["Company"]] = relationship(back_populates="organization")


class Company(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = uuid_pk()
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(200))
    cnpj: Mapped[str] = mapped_column(String(18), index=True, nullable=False)
    tax_regime: Mapped[str] = mapped_column(String(20), default="real", nullable=False)  # simples|presumido|real
    segment: Mapped[str | None] = mapped_column(String(80))
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    municipality: Mapped[str | None] = mapped_column(String(120))
    municipality_code: Mapped[str | None] = mapped_column(String(10))

    organization: Mapped[Organization] = relationship(back_populates="companies")
    branches: Mapped[list["Branch"]] = relationship(back_populates="company")


class Branch(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(18))
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    municipality: Mapped[str | None] = mapped_column(String(120))

    company: Mapped[Company] = relationship(back_populates="branches")
