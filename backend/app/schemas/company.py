import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import TAX_REGIMES, UFS

CNPJ_RE = re.compile(r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$")


def normalize_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        raise ValueError("CNPJ deve ter 14 dígitos")
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


class CompanyBase(BaseModel):
    legal_name: str = Field(min_length=2, max_length=200)
    trade_name: str | None = Field(default=None, max_length=200)
    cnpj: str
    tax_regime: str = "real"
    segment: str | None = Field(default=None, max_length=80)
    uf: str
    municipality: str | None = Field(default=None, max_length=120)
    municipality_code: str | None = Field(default=None, max_length=10)

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        if not CNPJ_RE.match(v.strip()):
            raise ValueError("CNPJ inválido")
        return normalize_cnpj(v)

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in UFS:
            raise ValueError("UF inválida")
        return v

    @field_validator("tax_regime")
    @classmethod
    def validate_regime(cls, v: str) -> str:
        if v not in TAX_REGIMES:
            raise ValueError(f"Regime deve ser um de: {sorted(TAX_REGIMES)}")
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    legal_name: str | None = Field(default=None, min_length=2, max_length=200)
    trade_name: str | None = None
    tax_regime: str | None = None
    segment: str | None = None
    uf: str | None = None
    municipality: str | None = None
    municipality_code: str | None = None

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v: str | None) -> str | None:
        if v is None:
            return v
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


class BranchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    cnpj: str | None = None
    uf: str
    municipality: str | None = None

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in UFS:
            raise ValueError("UF inválida")
        return v

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str | None) -> str | None:
        return normalize_cnpj(v) if v else None


class BranchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    cnpj: str | None
    uf: str
    municipality: str | None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    legal_name: str
    trade_name: str | None
    cnpj: str
    tax_regime: str
    segment: str | None
    uf: str
    municipality: str | None
    municipality_code: str | None
    branches: list[BranchOut] = []
