import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import or_, select

from app.api.v1.common import PageDep, paginate
from app.core.audit import audit
from app.core.deps import LEVEL_FISCAL, CurrentOrg, CurrentUser, DbSession, get_company_or_404, require_level
from app.models import Product, Service
from app.schemas.catalog import (
    CsvImportResult,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ServiceCreate,
    ServiceOut,
    ServiceUpdate,
)
from app.schemas.common import Page
from app.services import csv_import

router = APIRouter(tags=["Catálogo"])

MAX_CSV_BYTES = 5 * 1024 * 1024


async def _read_csv(file: UploadFile) -> bytes:
    if file.filename and not file.filename.lower().endswith(".csv"):
        raise HTTPException(422, "Envie um arquivo .csv")
    content = await file.read()
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(413, "Arquivo CSV acima de 5MB")
    return content


# --------------------------------- Produtos ---------------------------------

@router.get("/products", response_model=Page[ProductOut])
def list_products(
    db: DbSession, org: CurrentOrg, params: PageDep,
    company_id: uuid.UUID | None = None, search: str | None = None,
    ncm: str | None = None, uf: str | None = None,
):
    query = select(Product).where(Product.organization_id == org.id, Product.deleted_at.is_(None))
    if company_id:
        query = query.where(Product.company_id == company_id)
    if search:
        like = f"%{search}%"
        query = query.where(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.ncm.ilike(like)))
    if ncm:
        query = query.where(Product.ncm.startswith(ncm))
    if uf:
        query = query.where(or_(Product.origin_uf == uf.upper(), Product.dest_uf == uf.upper()))
    return paginate(db, query.order_by(Product.name), params)


@router.post("/products", response_model=ProductOut, status_code=201, dependencies=[require_level(LEVEL_FISCAL)])
def create_product(payload: ProductCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    get_company_or_404(db, org.id, payload.company_id)
    duplicate = db.scalar(select(Product).where(
        Product.organization_id == org.id, Product.company_id == payload.company_id,
        Product.sku == payload.sku, Product.deleted_at.is_(None),
    ))
    if duplicate:
        raise HTTPException(409, "SKU já cadastrado para esta empresa")
    product = Product(organization_id=org.id, **payload.model_dump())
    db.add(product)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="product.create",
          entity_type="product", entity_id=product.id, request=request)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut, dependencies=[require_level(LEVEL_FISCAL)])
def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: DbSession, org: CurrentOrg,
                   user: CurrentUser, request: Request):
    product = db.get(Product, product_id)
    if product is None or product.organization_id != org.id or product.deleted_at is not None:
        raise HTTPException(404, "Produto não encontrado")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(product, field, value)
    audit(db, organization_id=org.id, user=user, action="product.update",
          entity_type="product", entity_id=product.id, metadata={"changes": list(changes)}, request=request)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204, dependencies=[require_level(LEVEL_FISCAL)])
def delete_product(product_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    product = db.get(Product, product_id)
    if product is None or product.organization_id != org.id or product.deleted_at is not None:
        raise HTTPException(404, "Produto não encontrado")
    product.deleted_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="product.delete",
          entity_type="product", entity_id=product.id, request=request)
    db.commit()


@router.get("/products/csv-template", response_class=PlainTextResponse)
def product_csv_template(_user: CurrentUser):
    return PlainTextResponse(csv_import.PRODUCT_CSV_TEMPLATE, media_type="text/csv; charset=utf-8")


@router.post("/products/import-csv", response_model=CsvImportResult, dependencies=[require_level(LEVEL_FISCAL)])
async def import_products(
    db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request,
    company_id: uuid.UUID = Form(...), file: UploadFile = File(...),
):
    get_company_or_404(db, org.id, company_id)
    content = await _read_csv(file)
    result = csv_import.import_products_csv(db, org.id, company_id, content)
    audit(db, organization_id=org.id, user=user, action="product.import_csv",
          entity_type="company", entity_id=company_id,
          metadata={"created": result.created, "updated": result.updated, "errors": len(result.errors)},
          request=request)
    db.commit()
    return result


# --------------------------------- Serviços ---------------------------------

@router.get("/services", response_model=Page[ServiceOut])
def list_services(
    db: DbSession, org: CurrentOrg, params: PageDep,
    company_id: uuid.UUID | None = None, search: str | None = None,
):
    query = select(Service).where(Service.organization_id == org.id, Service.deleted_at.is_(None))
    if company_id:
        query = query.where(Service.company_id == company_id)
    if search:
        like = f"%{search}%"
        query = query.where(or_(Service.name.ilike(like), Service.code.ilike(like), Service.nbs.ilike(like)))
    return paginate(db, query.order_by(Service.name), params)


@router.post("/services", response_model=ServiceOut, status_code=201, dependencies=[require_level(LEVEL_FISCAL)])
def create_service(payload: ServiceCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    get_company_or_404(db, org.id, payload.company_id)
    duplicate = db.scalar(select(Service).where(
        Service.organization_id == org.id, Service.company_id == payload.company_id,
        Service.code == payload.code, Service.deleted_at.is_(None),
    ))
    if duplicate:
        raise HTTPException(409, "Código já cadastrado para esta empresa")
    service = Service(organization_id=org.id, **payload.model_dump())
    db.add(service)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="service.create",
          entity_type="service", entity_id=service.id, request=request)
    db.commit()
    db.refresh(service)
    return service


@router.put("/services/{service_id}", response_model=ServiceOut, dependencies=[require_level(LEVEL_FISCAL)])
def update_service(service_id: uuid.UUID, payload: ServiceUpdate, db: DbSession, org: CurrentOrg,
                   user: CurrentUser, request: Request):
    service = db.get(Service, service_id)
    if service is None or service.organization_id != org.id or service.deleted_at is not None:
        raise HTTPException(404, "Serviço não encontrado")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(service, field, value)
    audit(db, organization_id=org.id, user=user, action="service.update",
          entity_type="service", entity_id=service.id, metadata={"changes": list(changes)}, request=request)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/services/{service_id}", status_code=204, dependencies=[require_level(LEVEL_FISCAL)])
def delete_service(service_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    service = db.get(Service, service_id)
    if service is None or service.organization_id != org.id or service.deleted_at is not None:
        raise HTTPException(404, "Serviço não encontrado")
    service.deleted_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="service.delete",
          entity_type="service", entity_id=service.id, request=request)
    db.commit()


@router.get("/services/csv-template", response_class=PlainTextResponse)
def service_csv_template(_user: CurrentUser):
    return PlainTextResponse(csv_import.SERVICE_CSV_TEMPLATE, media_type="text/csv; charset=utf-8")


@router.post("/services/import-csv", response_model=CsvImportResult, dependencies=[require_level(LEVEL_FISCAL)])
async def import_services(
    db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request,
    company_id: uuid.UUID = Form(...), file: UploadFile = File(...),
):
    get_company_or_404(db, org.id, company_id)
    content = await _read_csv(file)
    result = csv_import.import_services_csv(db, org.id, company_id, content)
    audit(db, organization_id=org.id, user=user, action="service.import_csv",
          entity_type="company", entity_id=company_id,
          metadata={"created": result.created, "updated": result.updated, "errors": len(result.errors)},
          request=request)
    db.commit()
    return result
