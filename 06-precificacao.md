import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, uuid_pk

# Alíquotas em pontos percentuais (18.0000 = 18%). NUNCA hardcoded no motor:
# tudo que o cálculo usa vem destas tabelas + organizations.assumptions.


class TaxRule(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "tax_rules"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)  # null = org
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # Critérios de casamento (null = qualquer); ncm/nbs aceitam prefixo com '*' (ex.: '2202*')
    item_kind: Mapped[str] = mapped_column(String(10), default="any", nullable=False)  # product|service|any
    ncm_pattern: Mapped[str | None] = mapped_column(String(10), index=True)
    nbs_pattern: Mapped[str | None] = mapped_column(String(10))
    cfop: Mapped[str | None] = mapped_column(String(4))
    uf_origin: Mapped[str | None] = mapped_column(String(2))
    uf_dest: Mapped[str | None] = mapped_column(String(2))
    tax_regime: Mapped[str | None] = mapped_column(String(20))
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Sistema atual
    icms_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
    iss_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
    pis_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
    cofins_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
    ipi_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)

    # Sistema futuro (null em cbs/ibs = usar alíquota de referência das premissas da organização)
    cbs_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    ibs_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    is_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
    cbs_reduction_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"), nullable=False)
    ibs_reduction_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"), nullable=False)
    credit_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    legal_basis: Mapped[str | None] = mapped_column(String(255))  # ex.: 'LC 214/2025, art. 9º'
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)


class TaxTransitionYear(Base, TimestampMixin, TenantMixin):
    __tablename__ = "tax_transition_years"
    __table_args__ = (UniqueConstraint("organization_id", "year", name="uq_transition_org_year"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    # Fatores aplicados sobre a alíquota de referência (0..1); overrides em pontos percentuais
    cbs_factor: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"), nullable=False)
    ibs_factor: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"), nullable=False)
    cbs_rate_override: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))  # ex.: 0.9 no ano-teste 2026
    ibs_rate_override: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))  # ex.: 0.1 em 2026-2028
    cbs_adjustment_pp: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
    legacy_icms_iss_factor: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("1"), nullable=False)
    pis_cofins_factor: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("1"), nullable=False)
    selective_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    test_year_compensable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
