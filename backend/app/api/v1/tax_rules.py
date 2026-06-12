import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.api.v1.common import PageDep, paginate
from app.core.audit import audit
from app.core.deps import (
    LEVEL_ACCOUNTANT,
    LEVEL_FISCAL,
    CurrentOrg,
    CurrentUser,
    DbSession,
    get_company_or_404,
    require_level,
)
from app.models import TaxRule, TaxTransitionYear
from app.schemas.common import Page
from app.schemas.tax import TaxRuleCreate, TaxRuleOut, TaxRuleUpdate, TransitionYearOut, TransitionYearUpdate

router = APIRouter(tags=["Motor tributário"])


@router.get("/tax-rules", response_model=Page[TaxRuleOut])
def list_tax_rules(
    db: DbSession, org: CurrentOrg, params: PageDep,
    company_id: uuid.UUID | None = None, item_kind: str | None = None,
    active: bool | None = None, search: str | None = None,
):
    query = select(TaxRule).where(TaxRule.organization_id == org.id, TaxRule.deleted_at.is_(None))
    if company_id:
        query = query.where(TaxRule.company_id == company_id)
    if item_kind:
        query = query.where(TaxRule.item_kind == item_kind)
    if active is not None:
        query = query.where(TaxRule.is_active.is_(active))
    if search:
        query = query.where(TaxRule.name.ilike(f"%{search}%"))
    return paginate(db, query.order_by(TaxRule.priority.desc(), TaxRule.name), params)


@router.post("/tax-rules", response_model=TaxRuleOut, status_code=201, dependencies=[require_level(LEVEL_FISCAL)])
def create_tax_rule(payload: TaxRuleCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    if payload.company_id is not None:
        get_company_or_404(db, org.id, payload.company_id)
    rule = TaxRule(organization_id=org.id, **payload.model_dump())
    db.add(rule)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="tax_rule.create",
          entity_type="tax_rule", entity_id=rule.id, metadata={"name": rule.name}, request=request)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/tax-rules/{rule_id}", response_model=TaxRuleOut, dependencies=[require_level(LEVEL_FISCAL)])
def update_tax_rule(rule_id: uuid.UUID, payload: TaxRuleUpdate, db: DbSession, org: CurrentOrg,
                    user: CurrentUser, request: Request):
    rule = db.get(TaxRule, rule_id)
    if rule is None or rule.organization_id != org.id or rule.deleted_at is not None:
        raise HTTPException(404, "Regra não encontrada")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("company_id") is not None:
        get_company_or_404(db, org.id, changes["company_id"])
    for field, value in changes.items():
        setattr(rule, field, value)
    audit(db, organization_id=org.id, user=user, action="tax_rule.update",
          entity_type="tax_rule", entity_id=rule.id, metadata={"changes": list(changes)}, request=request)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/tax-rules/{rule_id}", status_code=204, dependencies=[require_level(LEVEL_FISCAL)])
def delete_tax_rule(rule_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    rule = db.get(TaxRule, rule_id)
    if rule is None or rule.organization_id != org.id or rule.deleted_at is not None:
        raise HTTPException(404, "Regra não encontrada")
    rule.deleted_at = datetime.now(timezone.utc)
    rule.is_active = False
    audit(db, organization_id=org.id, user=user, action="tax_rule.delete",
          entity_type="tax_rule", entity_id=rule.id, request=request)
    db.commit()


@router.get("/transition-years", response_model=list[TransitionYearOut])
def list_transition_years(db: DbSession, org: CurrentOrg):
    return db.scalars(
        select(TaxTransitionYear)
        .where(TaxTransitionYear.organization_id == org.id)
        .order_by(TaxTransitionYear.year)
    ).all()


@router.put("/transition-years/{year}", response_model=TransitionYearOut,
            dependencies=[require_level(LEVEL_ACCOUNTANT)])
def update_transition_year(year: int, payload: TransitionYearUpdate, db: DbSession, org: CurrentOrg,
                           user: CurrentUser, request: Request):
    """Parametrização administrativa dos fatores do ano — sem alteração de código."""
    row = db.scalar(select(TaxTransitionYear).where(
        TaxTransitionYear.organization_id == org.id, TaxTransitionYear.year == year
    ))
    if row is None:
        raise HTTPException(404, "Ano de transição não encontrado")
    changes = payload.model_dump(exclude_unset=True, exclude={"clear_cbs_override", "clear_ibs_override"})
    for field, value in changes.items():
        if value is not None:
            setattr(row, field, value)
    if payload.clear_cbs_override:
        row.cbs_rate_override = None
    if payload.clear_ibs_override:
        row.ibs_rate_override = None
    audit(db, organization_id=org.id, user=user, action="transition_year.update",
          entity_type="tax_transition_year", entity_id=row.id,
          metadata={"year": year, "changes": list(changes)}, request=request)
    db.commit()
    db.refresh(row)
    return row
