import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import COMPLIANCE_AREAS, COMPLIANCE_STATUSES, IMPACT_LEVELS, NORM_TYPES


# ----------------------------- Compliance ----------------------------------
class ComplianceTaskCreate(BaseModel):
    company_id: uuid.UUID
    area: str
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    status: str = "pendente"
    priority: str = "media"
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None
    evidence_url: str | None = Field(default=None, max_length=500)
    legal_update_id: uuid.UUID | None = None

    @field_validator("area")
    @classmethod
    def validate_area(cls, v: str) -> str:
        if v not in COMPLIANCE_AREAS:
            raise ValueError(f"Área deve ser uma de: {sorted(COMPLIANCE_AREAS)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in COMPLIANCE_STATUSES:
            raise ValueError(f"Status deve ser um de: {sorted(COMPLIANCE_STATUSES)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in {"baixa", "media", "alta"}:
            raise ValueError("Prioridade deve ser baixa, media ou alta")
        return v


class ComplianceTaskUpdate(BaseModel):
    area: str | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None
    evidence_url: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in COMPLIANCE_STATUSES:
            raise ValueError(f"Status deve ser um de: {sorted(COMPLIANCE_STATUSES)}")
        return v


class ComplianceTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    area: str
    title: str
    description: str | None
    status: str
    priority: str
    due_date: date | None
    assignee_id: uuid.UUID | None
    evidence_url: str | None
    legal_update_id: uuid.UUID | None
    created_at: datetime


class AreaSummary(BaseModel):
    area: str
    total: int
    done: int
    overdue: int
    progress_pct: float


class ComplianceSummary(BaseModel):
    overall_progress_pct: float
    total: int
    done: int
    overdue: int
    critical: int
    by_area: list[AreaSummary]


# --------------------------- Monitor legislativo ----------------------------
class LegalUpdateCreate(BaseModel):
    norm_type: str
    reference: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=255)
    summary: str | None = None
    impact: str = "medio"
    source_url: str | None = Field(default=None, max_length=500)
    published_at: date | None = None

    @field_validator("norm_type")
    @classmethod
    def validate_norm(cls, v: str) -> str:
        if v not in NORM_TYPES:
            raise ValueError(f"Tipo deve ser um de: {sorted(NORM_TYPES)}")
        return v

    @field_validator("impact")
    @classmethod
    def validate_impact(cls, v: str) -> str:
        if v not in IMPACT_LEVELS:
            raise ValueError(f"Impacto deve ser um de: {sorted(IMPACT_LEVELS)}")
        return v


class LegalUpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    norm_type: str
    reference: str
    title: str
    summary: str | None
    impact: str
    source_url: str | None
    published_at: date | None
    created_at: datetime


# ------------------------------- Auditoria ----------------------------------
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str | None
    entity_id: str | None
    extra: dict
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


# ------------------------------- API keys -----------------------------------
class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    company_id: uuid.UUID | None = None
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    company_id: uuid.UUID | None
    prefix: str
    rate_limit_per_minute: int
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyCreatedOut(BaseModel):
    api_key: ApiKeyOut
    secret: str  # exibido uma única vez


# ------------------------------- Relatórios ---------------------------------
class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID | None
    simulation_id: uuid.UUID | None
    report_type: str
    format: str
    premises: dict
    created_at: datetime


# ------------------------------- IA -----------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    answer: str
    disclaimer: str
    model: str | None
