"""Documentos fiscais e créditos — tabelas criadas no MVP, populadas nas fases 2 e 3."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, uuid_pk
from app.models.org import JSONType


class Invoice(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(10), nullable=False)  # nfe|nfce|nfse|cte
    access_key: Mapped[str | None] = mapped_column(String(44), unique=True)
    number: Mapped[str | None] = mapped_column(String(20))
    series: Mapped[str | None] = mapped_column(String(5))
    direction: Mapped[str] = mapped_column(String(3), default="out", nullable=False)  # in|out
    partner_name: Mapped[str | None] = mapped_column(String(200))
    partner_cnpj: Mapped[str | None] = mapped_column(String(18))
    uf_origin: Mapped[str | None] = mapped_column(String(2))
    uf_dest: Mapped[str | None] = mapped_column(String(2))
    issued_at: Mapped[date | None] = mapped_column(Date)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="importado", nullable=False)
    xml_path: Mapped[str | None] = mapped_column(String(500))

    items: Mapped[list["InvoiceItem"]] = relationship(back_populates="invoice")


class InvoiceItem(Base, TimestampMixin):
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    invoice_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("invoices.id"), index=True, nullable=False)
    line: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ncm: Mapped[str | None] = mapped_column(String(8))
    cfop: Mapped[str | None] = mapped_column(String(4))
    cst: Mapped[str | None] = mapped_column(String(4))
    description: Mapped[str | None] = mapped_column(String(300))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("1"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    icms_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    pis_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    cofins_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    ipi_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    iss_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="items")


class TaxCredit(Base, TimestampMixin, TenantMixin):
    __tablename__ = "tax_credits"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True, nullable=False)
    invoice_item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("invoice_items.id"), index=True)
    regime: Mapped[str] = mapped_column(String(10), nullable=False)  # atual|cbs_ibs
    credit_type: Mapped[str] = mapped_column(String(30), nullable=False)  # icms|pis_cofins|cbs|ibs
    status: Mapped[str] = mapped_column(String(15), default="potencial", nullable=False)  # apurado|potencial|perdido|em_risco
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)  # trilha de auditoria
