import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.common import PageDep, paginate
from app.core.audit import audit
from app.core.deps import (
    LEVEL_ACCOUNTANT,
    LEVEL_CONSULTANT,
    CurrentOrg,
    CurrentUser,
    DbSession,
    get_company_or_404,
    require_level,
)
from app.models import ComplianceTask
from app.schemas.common import Page
from app.schemas.governance import ComplianceSummary, ComplianceTaskCreate, ComplianceTaskOut, ComplianceTaskUpdate
from app.services.checklist_template import CHECKLIST_TEMPLATE
from app.services.dashboard_service import compliance_summary

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/tasks", response_model=Page[ComplianceTaskOut])
def list_tasks(
    db: DbSession, org: CurrentOrg, params: PageDep,
    company_id: uuid.UUID | None = None, area: str | None = None, status: str | None = None,
):
    query = select(ComplianceTask).where(
        ComplianceTask.organization_id == org.id, ComplianceTask.deleted_at.is_(None)
    )
    if company_id:
        query = query.where(ComplianceTask.company_id == company_id)
    if area:
        query = query.where(ComplianceTask.area == area)
    if status:
        query = query.where(ComplianceTask.status == status)
    return paginate(db, query.order_by(ComplianceTask.due_date.is_(None), ComplianceTask.due_date), params)


@router.post("/tasks", response_model=ComplianceTaskOut, status_code=201,
             dependencies=[require_level(LEVEL_CONSULTANT)])
def create_task(payload: ComplianceTaskCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    get_company_or_404(db, org.id, payload.company_id)
    task = ComplianceTask(organization_id=org.id, **payload.model_dump())
    db.add(task)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="compliance_task.create",
          entity_type="compliance_task", entity_id=task.id, request=request)
    db.commit()
    db.refresh(task)
    return task


@router.put("/tasks/{task_id}", response_model=ComplianceTaskOut, dependencies=[require_level(LEVEL_CONSULTANT)])
def update_task(task_id: uuid.UUID, payload: ComplianceTaskUpdate, db: DbSession, org: CurrentOrg,
                user: CurrentUser, request: Request):
    task = db.get(ComplianceTask, task_id)
    if task is None or task.organization_id != org.id or task.deleted_at is not None:
        raise HTTPException(404, "Tarefa não encontrada")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(task, field, value)
    audit(db, organization_id=org.id, user=user, action="compliance_task.update",
          entity_type="compliance_task", entity_id=task.id, metadata={"changes": list(changes)}, request=request)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204, dependencies=[require_level(LEVEL_CONSULTANT)])
def delete_task(task_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    task = db.get(ComplianceTask, task_id)
    if task is None or task.organization_id != org.id or task.deleted_at is not None:
        raise HTTPException(404, "Tarefa não encontrada")
    task.deleted_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="compliance_task.delete",
          entity_type="compliance_task", entity_id=task.id, request=request)
    db.commit()


class ApplyTemplateRequest(BaseModel):
    company_id: uuid.UUID


@router.post("/apply-template", response_model=dict, dependencies=[require_level(LEVEL_ACCOUNTANT)])
def apply_template(payload: ApplyTemplateRequest, db: DbSession, org: CurrentOrg, user: CurrentUser,
                   request: Request):
    """Aplica o checklist padrão da Reforma (21 tarefas em 7 áreas) à empresa."""
    company = get_company_or_404(db, org.id, payload.company_id)
    existing_titles = set(
        db.scalars(
            select(ComplianceTask.title).where(
                ComplianceTask.organization_id == org.id,
                ComplianceTask.company_id == company.id,
                ComplianceTask.deleted_at.is_(None),
            )
        ).all()
    )
    created = 0
    base_due = date.today() + timedelta(days=60)
    for index, template_task in enumerate(CHECKLIST_TEMPLATE):
        if template_task["title"] in existing_titles:
            continue
        db.add(ComplianceTask(
            organization_id=org.id, company_id=company.id,
            area=template_task["area"], title=template_task["title"],
            description=template_task["description"], priority=template_task["priority"],
            status="pendente",
            due_date=base_due + timedelta(days=7 * (index // 5)),
        ))
        created += 1
    audit(db, organization_id=org.id, user=user, action="compliance.apply_template",
          entity_type="company", entity_id=company.id, metadata={"created": created}, request=request)
    db.commit()
    return {"created": created}


@router.get("/summary", response_model=ComplianceSummary)
def get_summary(db: DbSession, org: CurrentOrg, company_id: uuid.UUID | None = None):
    return compliance_summary(db, org.id, company_id)
