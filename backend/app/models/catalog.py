import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, uuid_pk


class Product(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("organization_id", "company_id", "sku", name="uq_products_org_company_sku"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ncm: Mapped[str] = mapped_column(String(8), index=True, nullable=False)
    cest: Mapped[str | None] = mapped_column(String(9))
    cfop: Mapped[str | None] = mapped_column(String(4))
    cst_icms: Mapped[str | None] = mapped_column(String(3))
    csosn: Mapped[str | None] = mapped_column(String(4))
    origin_uf: Mapped[str | None] = mapped_column(String(2))
    dest_uf: Mapped[str | None] = mapped_column(String(2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    monthly_volume: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    is_selective: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # candidato a IS


class Service(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "services"
    __table_args__ = (UniqueConstraint("organization_id", "company_id", "code", name="uq_services_org_company_code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    nbs: Mapped[str | None] = mapped_column(String(9), index=True)
    lc116_item: Mapped[str | None] = mapped_column(String(10))
    municipality: Mapped[str | None] = mapped_column(String(120))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    monthly_volume: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
