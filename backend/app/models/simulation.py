import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, uuid_pk
from app.models.org import JSONType


class Simulation(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    scenario: Mapped[str] = mapped_column(String(15), default="provavel", nullable=False)
    year_start: Mapped[int] = mapped_column(Integer, nullable=False)
    year_end: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="concluida", nullable=False)
    origin: Mapped[str] = mapped_column(String(15), default="manual", nullable=False)  # manual|diagnostico
    # Snapshot das premissas usadas (rastreabilidade) e resumo agregado por ano
    assumptions_snapshot: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    items: Mapped[list["SimulationItem"]] = relationship(back_populates="simulation")


class SimulationItem(Base, TimestampMixin):
    __tablename__ = "simulation_items"
    __table_args__ = (Index("ix_simulation_items_sim_year", "simulation_id", "year"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    simulation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("simulations.id"), index=True, nullable=False)
    item_kind: Mapped[str] = mapped_column(String(10), nullable=False)  # product|service
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("tax_rules.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    annual_revenue: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    current_tax_total: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    current_credits: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    current_net_burden: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    future_cbs: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    future_ibs: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    future_is: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    future_legacy: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    future_credits: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    future_net_burden: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    delta_net: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)
    margin_current_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    margin_future_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    breakeven_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    cash_flow_impact: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"), nullable=False)

    # Memoria de calculo completa: regra, aliquotas, fatores, formulas, premissas, avisos
    calc_memory: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    simulation: Mapped[Simulation] = relationship(back_populates="items")
