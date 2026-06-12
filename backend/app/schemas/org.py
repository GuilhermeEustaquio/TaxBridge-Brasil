import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Premissas configuráveis do motor tributário.
# Defaults = estimativas públicas (Ministério da Fazenda / mercado) para a
# alíquota de referência. NÃO são alíquotas oficiais definitivas — o admin
# pode (e deve) ajustá-las conforme a regulamentação evoluir. Ver docs/04.
# ---------------------------------------------------------------------------


class ScenarioAdjustment(BaseModel):
    rate_delta_pp: Decimal = Field(default=Decimal("0"), ge=-10, le=10, description="Ajuste em p.p. sobre CBS+IBS")


def _default_scenarios() -> dict[str, ScenarioAdjustment]:
    return {
        "conservador": ScenarioAdjustment(rate_delta_pp=Decimal("1.5")),
        "provavel": ScenarioAdjustment(rate_delta_pp=Decimal("0")),
        "agressivo": ScenarioAdjustment(rate_delta_pp=Decimal("-1.0")),
    }


class Assumptions(BaseModel):
    cbs_reference_rate: Decimal = Field(default=Decimal("8.8"), ge=0, le=30)
    ibs_reference_rate: Decimal = Field(default=Decimal("17.7"), ge=0, le=40)
    input_cost_creditable_ratio: Decimal = Field(default=Decimal("0.60"), ge=0, le=1)
    current_credit_efficiency: Decimal = Field(default=Decimal("0.70"), ge=0, le=1)
    future_credit_efficiency: Decimal = Field(default=Decimal("0.95"), ge=0, le=1)
    split_payment_enabled: bool = True
    split_payment_float_days: int = Field(default=40, ge=0, le=365)
    cost_of_capital_annual: Decimal = Field(default=Decimal("0.12"), ge=0, le=1)
    simples_effective_rate: Decimal = Field(default=Decimal("8.0"), ge=0, le=33)
    icms_inside_price: bool = True
    scenario_adjustments: dict[str, ScenarioAdjustment] = Field(default_factory=_default_scenarios)


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    plan: str
    assumptions: Assumptions
