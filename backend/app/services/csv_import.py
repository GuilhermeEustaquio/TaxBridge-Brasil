"""Importação de catálogo via CSV com validação linha a linha.

Aceita separador ',' ou ';' (detecção automática) e decimal com vírgula ou ponto.
Upsert por SKU/código dentro da empresa. Erros não interrompem o lote: cada linha
inválida volta no relatório com o motivo.
"""

import csv
import io
import uuid
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, Service
from app.schemas.catalog import CsvImportResult, CsvRowError, ProductBase, ServiceBase

PRODUCT_COLUMNS = ["sku", "nome", "ncm", "cest", "cfop", "cst_icms", "csosn", "uf_origem",
                   "uf_destino", "preco_unitario", "custo_unitario", "volume_mensal", "seletivo"]
SERVICE_COLUMNS = ["codigo", "nome", "nbs", "item_lc116", "municipio",
                   "preco_unitario", "custo_unitario", "volume_mensal"]

PRODUCT_CSV_TEMPLATE = (
    ";".join(PRODUCT_COLUMNS) + "\n"
    "SKU-001;Arroz branco 5kg;10063021;;5102;000;;SP;SP;25,90;18,00;1200;nao\n"
    "SKU-002;Refrigerante cola 2L;22021000;0300700;5102;000;;SP;RJ;9,50;4,20;5000;sim\n"
)
SERVICE_CSV_TEMPLATE = (
    ";".join(SERVICE_COLUMNS) + "\n"
    "SRV-001;Consultoria tributária;1.1501;17.01;São Paulo;350,00;120,00;80\n"
)


def _parse_decimal(value: str | None, default: Decimal | None = None) -> Decimal | None:
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().replace(".", "").replace(",", ".") if "," in value else value.strip()
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"número inválido: '{value}'") from exc


def _parse_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"sim", "s", "true", "1", "yes"}


def _read_rows(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig", errors="replace")
    sample = text[:2048]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if reader.fieldnames:
        reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]
    return [row for row in reader]


def _first_error_message(exc: ValidationError) -> str:
    err = exc.errors()[0]
    field = ".".join(str(p) for p in err["loc"])
    return f"{field}: {err['msg']}"


def import_products_csv(db: Session, organization_id: uuid.UUID, company_id: uuid.UUID, content: bytes) -> CsvImportResult:
    created = updated = 0
    errors: list[CsvRowError] = []
    for index, row in enumerate(_read_rows(content), start=2):  # linha 1 = cabeçalho
        try:
            data = ProductBase(
                sku=(row.get("sku") or "").strip(),
                name=(row.get("nome") or "").strip(),
                ncm=(row.get("ncm") or "").strip(),
                cest=(row.get("cest") or "").strip() or None,
                cfop=(row.get("cfop") or "").strip() or None,
                cst_icms=(row.get("cst_icms") or "").strip() or None,
                csosn=(row.get("csosn") or "").strip() or None,
                origin_uf=(row.get("uf_origem") or "").strip() or None,
                dest_uf=(row.get("uf_destino") or "").strip() or None,
                unit_price=_parse_decimal(row.get("preco_unitario"), Decimal("0")),
                unit_cost=_parse_decimal(row.get("custo_unitario"), Decimal("0")),
                monthly_volume=_parse_decimal(row.get("volume_mensal"), Decimal("0")),
                is_selective=_parse_bool(row.get("seletivo")),
            )
        except ValidationError as exc:
            errors.append(CsvRowError(line=index, error=_first_error_message(exc)))
            continue
        except ValueError as exc:
            errors.append(CsvRowError(line=index, error=str(exc)))
            continue

        existing = db.scalar(
            select(Product).where(
                Product.organization_id == organization_id,
                Product.company_id == company_id,
                Product.sku == data.sku,
                Product.deleted_at.is_(None),
            )
        )
        if existing:
            for field_name, value in data.model_dump(exclude={"sku"}).items():
                setattr(existing, field_name, value)
            updated += 1
        else:
            db.add(Product(organization_id=organization_id, company_id=company_id, **data.model_dump()))
            created += 1
    return CsvImportResult(created=created, updated=updated, errors=errors)


def import_services_csv(db: Session, organization_id: uuid.UUID, company_id: uuid.UUID, content: bytes) -> CsvImportResult:
    created = updated = 0
    errors: list[CsvRowError] = []
    for index, row in enumerate(_read_rows(content), start=2):
        try:
            data = ServiceBase(
                code=(row.get("codigo") or "").strip(),
                name=(row.get("nome") or "").strip(),
                nbs=(row.get("nbs") or "").strip() or None,
                lc116_item=(row.get("item_lc116") or "").strip() or None,
                municipality=(row.get("municipio") or "").strip() or None,
                unit_price=_parse_decimal(row.get("preco_unitario"), Decimal("0")),
                unit_cost=_parse_decimal(row.get("custo_unitario"), Decimal("0")),
                monthly_volume=_parse_decimal(row.get("volume_mensal"), Decimal("0")),
            )
        except ValidationError as exc:
            errors.append(CsvRowError(line=index, error=_first_error_message(exc)))
            continue
        except ValueError as exc:
            errors.append(CsvRowError(line=index, error=str(exc)))
            continue

        existing = db.scalar(
            select(Service).where(
                Service.organization_id == organization_id,
                Service.company_id == company_id,
                Service.code == data.code,
                Service.deleted_at.is_(None),
            )
        )
        if existing:
            for field_name, value in data.model_dump(exclude={"code"}).items():
                setattr(existing, field_name, value)
            updated += 1
        else:
            db.add(Service(organization_id=organization_id, company_id=company_id, **data.model_dump()))
            created += 1
    return CsvImportResult(created=created, updated=updated, errors=errors)
