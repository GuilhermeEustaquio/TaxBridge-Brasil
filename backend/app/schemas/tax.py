import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import TAX_REGIMES, UFS


class TaxRuleBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    company_id: uuid.UUID | None = None
    item_kind: str = "any"
    ncm_pattern: str | None = Field(default=None, max_length=10)
    nbs_pattern: str | None = Field(default=None, max_length=10)
    cfop: str | None = Field(default=None, max_length=4)
    uf_origin: str | None = None
    uf_dest: str | None = None
    tax_regime: str | None = None
    priority: int = Field(default=0, ge=0, le=1000)

    icms_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    iss_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    pis_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    cofins_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    ipi_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)

    cbs_rate: Decimal | None = Field(default=None, ge=0, le=100)
    ibs_rate: Decimal | None = Field(default=None, ge=0, le=100)
    is_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    cbs_reduction_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    ibs_reduction_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    credit_allowed: bool = True

    legal_basis: str | None = Field(default=None, max_length=255)
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool = True

    @field_validator("item_kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        if v not in {"product", "service", "any"}:
            raise ValueError("item_kind deve ser product, service ou any")
        return v

    @field_validator("uf_origin", "uf_dest")
    @classmethod
    def validate_uf(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        v = v.strip().upper()
        if v not in UFS:
            raise ValueError("UF inválida")
        return v

    @field_validator("tax_regime")
    @classmethod
    def validate_regime(cls, v: str | None) -> str | None:
        if v is not None and v not in TAX_REGIMES:
            raise ValueError(f"Regime deve ser um de: {sorted(TAX_REGIMES)}")
        return v


class TaxRuleCreate(TaxRuleBase):
    pass


class TaxRuleUpdate(TaxRuleBase):
    name: str | None = Field(default=None, min_length=2, max_length=160)  # type: ignore[assignment]


class TaxRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    company_id: uuid.UUID | None
    item_kind: str
    ncm_pattern: str | None
    nbs_pattern: str | None
    cfop: str | None
    uf_origin: str | None
    uf_dest: str | None
    tax_regime: str | None
    priority: int
    icms_rate: float
    iss_rate: float
    pis_rate: float
    cofins_rate: float
    ipi_rate: float
    cbs_rate: float | None
    ibs_rate: float | None
    is_rate: float
    cbs_reduction_pct: float
    ibs_reduction_pct: float
    credit_allowed: bool
    legal_basis: str | None
    valid_from: date | None
    valid_to: date | None
    is_active: bool


class TransitionYearOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    year: int
    cbs_factor: float
    ibs_factor: float
    cbs_rate_override: float | None
    ibs_rate_override: float | None
    cbs_adjustment_pp: float
    legacy_icms_iss_factor: float
    pis_cofins_factor: float
    selective_active: bool
    test_year_compensable: bool
    notes: str | None


class TransitionYearUpdate(BaseModel):
    cbs_factor: Decimal | None = Field(default=None, ge=0, le=1)
    ibs_factor: Decimal | None = Field(default=None, ge=0, le=1)
    cbs_rate_override: Decimal | None = Field(default=None, ge=0, le=100)
    ibs_rate_override: Decimal | None = Field(default=None, ge=0, le=100)
    cbs_adjustment_pp: Decimal | None = Field(default=None, ge=-10, le=10)
    legacy_icms_iss_factor: Decimal | None = Field(default=None, ge=0, le=1)
    pis_cofins_factor: Decimal | None = Field(default=None, ge=0, le=1)
    selective_active: bool | None = None
    test_year_compensable: bool | None = None
    notes: str | None = None
    clear_cbs_override: bool = False
    clear_ibs_override: bool = False
