from fastapi import APIRouter, Request

from app.core.audit import audit
from app.core.deps import LEVEL_ACCOUNTANT, CurrentOrg, CurrentUser, DbSession, require_level
from app.schemas.org import Assumptions, OrganizationOut

router = APIRouter(prefix="/organizations", tags=["Organização"])


@router.get("/me", response_model=OrganizationOut)
def get_my_organization(org: CurrentOrg):
    return org


@router.put("/assumptions", response_model=OrganizationOut, dependencies=[require_level(LEVEL_ACCOUNTANT)])
def update_assumptions(payload: Assumptions, org: CurrentOrg, user: CurrentUser, db: DbSession, request: Request):
    """Atualiza as premissas configuráveis do motor (sem deploy, com auditoria)."""
    before = org.assumptions
    org.assumptions = payload.model_dump(mode="json")
    audit(db, organization_id=org.id, user=user, action="organization.assumptions.update",
          entity_type="organization", entity_id=org.id,
          metadata={"before": before, "after": org.assumptions}, request=request)
    db.commit()
    db.refresh(org)
    return org
