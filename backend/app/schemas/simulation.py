import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import SCENARIOS


class SimulationCreate(BaseModel):
    company_id: uuid.UUID
    name: str = Field(min_length=2, max_length=200)
    scenario: str = "provavel"
    year_start: int = Field(default=2026, ge=2026, le=2033)
    year_end: int = Field(default=2033, ge=2026, le=2033)
    assumptions_override: dict | None = None  # overrides pontuais de premissas (auditados no snapshot)

    @field_validator("scenario")
    @classmethod
    def validate_scenario(cls, v: str) -> str:
        if v not in SCENARIOS:
            raise ValueError(f"Cenário deve ser um de: {sorted(SCENARIOS)}")
        return v

    @model_validator(mode="after")
    def validate_years(self) -> "SimulationCreate":
        if self.year_end < self.year_start:
            raise ValueError("year_end deve ser maior ou igual a year_start")
        return self


class SimulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    scenario: str
    year_start: int
    year_end: int
    status: str
    origin: str
    summary: dict
    assumptions_snapshot: dict
    created_at: datetime


class SimulationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    scenario: str
    year_start: int
    year_end: int
    status: str
    origin: str
    created_at: datetime


class SimulationItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_kind: str
    item_id: uuid.UUID
    item_name: str
    tax_rule_id: uuid.UUID | None
    year: int
    annual_revenue: float
    current_tax_total: float
    current_credits: float
    current_net_burden: float
    future_cbs: float
    future_ibs: float
    future_is: float
    future_legacy: float
    future_credits: float
    future_net_burden: float
    delta_net: float
    margin_current_pct: float | None
    margin_future_pct: float | None
    breakeven_price: float | None
    cash_flow_impact: float
    calc_memory: dict
