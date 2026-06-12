import re
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import UFS


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=2, max_length=200)
    ncm: str
    cest: str | None = Field(default=None, max_length=9)
    cfop: str | None = Field(default=None, max_length=4)
    cst_icms: str | None = Field(default=None, max_length=3)
    csosn: str | None = Field(default=None, max_length=4)
    origin_uf: str | None = None
    dest_uf: str | None = None
    unit_price: Decimal = Field(ge=0, le=Decimal("999999999"))
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    monthly_volume: Decimal = Field(default=Decimal("0"), ge=0)
    is_selective: bool = False

    @field_validator("ncm")
    @classmethod
    def validate_ncm(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) != 8:
            raise ValueError("NCM deve ter 8 dígitos")
        return digits

    @field_validator("origin_uf", "dest_uf")
    @classmethod
    def validate_uf(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        v = v.strip().upper()
        if v not in UFS:
            raise ValueError("UF inválida")
        return v


class ProductCreate(ProductBase):
    company_id: uuid.UUID


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    ncm: str | None = None
    cest: str | None = None
    cfop: str | None = None
    cst_icms: str | None = None
    csosn: str | None = None
    origin_uf: str | None = None
    dest_uf: str | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    monthly_volume: Decimal | None = Field(default=None, ge=0)
    is_selective: bool | None = None

    @field_validator("ncm")
    @classmethod
    def validate_ncm(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) != 8:
            raise ValueError("NCM deve ter 8 dígitos")
        return digits


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    sku: str
    name: str
    ncm: str
    cest: str | None
    cfop: str | None
    cst_icms: str | None
    csosn: str | None
    origin_uf: str | None
    dest_uf: str | None
    unit_price: float
    unit_cost: float
    monthly_volume: float
    is_selective: bool


class ServiceBase(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=2, max_length=200)
    nbs: str | None = Field(default=None, max_length=9)
    lc116_item: str | None = Field(default=None, max_length=10)
    municipality: str | None = Field(default=None, max_length=120)
    unit_price: Decimal = Field(ge=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    monthly_volume: Decimal = Field(default=Decimal("0"), ge=0)


class ServiceCreate(ServiceBase):
    company_id: uuid.UUID


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    nbs: str | None = None
    lc116_item: str | None = None
    municipality: str | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    monthly_volume: Decimal | None = Field(default=None, ge=0)


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    code: str
    name: str
    nbs: str | None
    lc116_item: str | None
    municipality: str | None
    unit_price: float
    unit_cost: float
    monthly_volume: float


class CsvRowError(BaseModel):
    line: int
    error: str


class CsvImportResult(BaseModel):
    created: int
    updated: int
    errors: list[CsvRowError]
