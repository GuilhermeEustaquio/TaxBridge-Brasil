from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

TAX_REGIMES = {"simples", "presumido", "real"}
SCENARIOS = {"conservador", "provavel", "agressivo"}
COMPLIANCE_AREAS = {"fiscal", "contabil", "financeiro", "juridico", "ti", "vendas", "compras"}
COMPLIANCE_STATUSES = {"pendente", "em_andamento", "concluido", "vencido", "critico"}
IMPACT_LEVELS = {"baixo", "medio", "alto", "critico"}
NORM_TYPES = {"lei", "lc", "decreto", "nota_tecnica", "portaria", "outro"}


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class Msg(BaseModel):
    detail: str
