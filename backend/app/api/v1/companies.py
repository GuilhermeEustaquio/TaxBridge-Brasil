import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import or_, select

from app.api.v1.common import PageDep, paginate
from app.core.audit import audit
from app.core.deps import (
    LEVEL_FISCAL,
    LEVEL_OWNER,
    CurrentOrg,
    CurrentUser,
    DbSession,
    get_company_or_404,
    require_level,
)
from app.models import Branch, Company
from app.schemas.common import Page
from app.schemas.company import BranchCreate, BranchOut, CompanyCreate, CompanyOut, CompanyUpdate
from app.schemas.simulation import SimulationOut
from app.services.simulation_service import run_simulation

router = APIRouter(prefix="/companies", tags=["Empresas"])


@router.get("", response_model=Page[CompanyOut])
def list_companies(
    db: DbSession,
    org: CurrentOrg,
    params: PageDep,
    search: str | None = None,
    uf: str | None = None,
    tax_regime: str | None = None,
):
    query = select(Company).where(Company.organization_id == org.id, Company.deleted_at.is_(None))
    if search:
        like = f"%{search}%"
        query = query.where(or_(Company.legal_name.ilike(like), Company.trade_name.ilike(like), Company.cnpj.ilike(like)))
    if uf:
        query = query.where(Company.uf == uf.upper())
    if tax_regime:
        query = query.where(Company.tax_regime == tax_regime)
    return paginate(db, query.order_by(Company.legal_name), params)


@router.post("", response_model=CompanyOut, status_code=201, dependencies=[require_level(LEVEL_FISCAL)])
def create_company(payload: CompanyCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    duplicate = db.scalar(
        select(Company).where(
            Company.organization_id == org.id, Company.cnpj == payload.cnpj, Company.deleted_at.is_(None)
        )
    )
    if duplicate:
        raise HTTPException(409, "CNPJ já cadastrado nesta organização")
    company = Company(organization_id=org.id, **payload.model_dump())
    db.add(company)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="company.create",
          entity_type="company", entity_id=company.id, metadata={"cnpj": company.cnpj}, request=request)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: uuid.UUID, db: DbSession, org: CurrentOrg):
    return get_company_or_404(db, org.id, company_id)


@router.put("/{company_id}", response_model=CompanyOut, dependencies=[require_level(LEVEL_FISCAL)])
def update_company(company_id: uuid.UUID, payload: CompanyUpdate, db: DbSession, org: CurrentOrg,
                   user: CurrentUser, request: Request):
    company = get_company_or_404(db, org.id, company_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in changes.items():
        setattr(company, field, value)
    audit(db, organization_id=org.id, user=user, action="company.update",
          entity_type="company", entity_id=company.id, metadata={"changes": list(changes)}, request=request)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204, dependencies=[require_level(LEVEL_OWNER)])
def delete_company(company_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    company = get_company_or_404(db, org.id, company_id)
    company.deleted_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="company.delete",
          entity_type="company", entity_id=company.id, request=request)
    db.commit()


@router.get("/{company_id}/branches", response_model=list[BranchOut])
def list_branches(company_id: uuid.UUID, db: DbSession, org: CurrentOrg):
    company = get_company_or_404(db, org.id, company_id)
    return db.scalars(
        select(Branch).where(Branch.company_id == company.id, Branch.deleted_at.is_(None)).order_by(Branch.name)
    ).all()


@router.post("/{company_id}/branches", response_model=BranchOut, status_code=201,
             dependencies=[require_level(LEVEL_FISCAL)])
def create_branch(company_id: uuid.UUID, payload: BranchCreate, db: DbSession, org: CurrentOrg,
                  user: CurrentUser, request: Request):
    company = get_company_or_404(db, org.id, company_id)
    branch = Branch(organization_id=org.id, company_id=company.id, **payload.model_dump())
    db.add(branch)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="branch.create",
          entity_type="branch", entity_id=branch.id, request=request)
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{company_id}/branches/{branch_id}", status_code=204, dependencies=[require_level(LEVEL_FISCAL)])
def delete_branch(company_id: uuid.UUID, branch_id: uuid.UUID, db: DbSession, org: CurrentOrg,
                  user: CurrentUser, request: Request):
    company = get_company_or_404(db, org.id, company_id)
    branch = db.get(Branch, branch_id)
    if branch is None or branch.company_id != company.id or branch.deleted_at is not None:
        raise HTTPException(404, "Filial não encontrada")
    branch.deleted_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="branch.delete",
          entity_type="branch", entity_id=branch.id, request=request)
    db.commit()


@router.post("/{company_id}/diagnostico", response_model=SimulationOut, status_code=201,
             dependencies=[require_level(LEVEL_FISCAL)])
def run_diagnostic(company_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    """★ Diagnóstico em 1 clique: simulação completa 2026–2033, cenário provável."""
    company = get_company_or_404(db, org.id, company_id)
    simulation = run_simulation(
        db, organization_id=org.id, company=company, user=user,
        name=f"Diagnóstico automático — {company.legal_name}",
        scenario="provavel", year_start=2026, year_end=2033, origin="diagnostico",
    )
    audit(db, organization_id=org.id, user=user, action="simulation.diagnostic",
          entity_type="simulation", entity_id=simulation.id, request=request)
    db.commit()
    db.refresh(simulation)
    return simulation
