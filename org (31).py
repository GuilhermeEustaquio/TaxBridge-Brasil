"""Routers menores: monitor legislativo, dashboard, auditoria, API keys, relatórios e IA."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import or_, select

from app.api.v1.common import PageDep, paginate
from app.core.audit import audit
from app.core.deps import (
    LEVEL_ACCOUNTANT,
    LEVEL_CONSULTANT,
    LEVEL_FISCAL,
    LEVEL_OWNER,
    CurrentOrg,
    CurrentUser,
    DbSession,
    require_level,
)
from app.core.security import generate_api_key
from app.models import AIConversation, ApiKey, AuditLog, LegalUpdate, Report
from app.schemas.common import Page
from app.schemas.governance import (
    ApiKeyCreate,
    ApiKeyCreatedOut,
    ApiKeyOut,
    AuditLogOut,
    ChatRequest,
    ChatResponse,
    LegalUpdateCreate,
    LegalUpdateOut,
    ReportOut,
)
from app.services import ai_assistant
from app.services.dashboard_service import build_dashboard

# ------------------------------ Monitor legislativo -------------------------
legal_router = APIRouter(prefix="/legal-updates", tags=["Monitor legislativo"])


@legal_router.get("", response_model=Page[LegalUpdateOut])
def list_legal_updates(
    db: DbSession, org: CurrentOrg, params: PageDep,
    impact: str | None = None, norm_type: str | None = None, search: str | None = None,
):
    query = select(LegalUpdate).where(LegalUpdate.organization_id == org.id, LegalUpdate.deleted_at.is_(None))
    if impact:
        query = query.where(LegalUpdate.impact == impact)
    if norm_type:
        query = query.where(LegalUpdate.norm_type == norm_type)
    if search:
        like = f"%{search}%"
        query = query.where(or_(LegalUpdate.title.ilike(like), LegalUpdate.reference.ilike(like)))
    return paginate(db, query.order_by(LegalUpdate.published_at.desc().nullslast()), params)


@legal_router.post("", response_model=LegalUpdateOut, status_code=201, dependencies=[require_level(LEVEL_FISCAL)])
def create_legal_update(payload: LegalUpdateCreate, db: DbSession, org: CurrentOrg, user: CurrentUser,
                        request: Request):
    update = LegalUpdate(organization_id=org.id, **payload.model_dump())
    db.add(update)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="legal_update.create",
          entity_type="legal_update", entity_id=update.id, request=request)
    db.commit()
    db.refresh(update)
    return update


@legal_router.put("/{update_id}", response_model=LegalUpdateOut, dependencies=[require_level(LEVEL_FISCAL)])
def update_legal_update(update_id: uuid.UUID, payload: LegalUpdateCreate, db: DbSession, org: CurrentOrg,
                        user: CurrentUser, request: Request):
    update = db.get(LegalUpdate, update_id)
    if update is None or update.organization_id != org.id or update.deleted_at is not None:
        raise HTTPException(404, "Norma não encontrada")
    for field, value in payload.model_dump().items():
        setattr(update, field, value)
    audit(db, organization_id=org.id, user=user, action="legal_update.update",
          entity_type="legal_update", entity_id=update.id, request=request)
    db.commit()
    db.refresh(update)
    return update


@legal_router.delete("/{update_id}", status_code=204, dependencies=[require_level(LEVEL_FISCAL)])
def delete_legal_update(update_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    update = db.get(LegalUpdate, update_id)
    if update is None or update.organization_id != org.id or update.deleted_at is not None:
        raise HTTPException(404, "Norma não encontrada")
    update.deleted_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="legal_update.delete",
          entity_type="legal_update", entity_id=update.id, request=request)
    db.commit()


# ------------------------------ Dashboard -----------------------------------
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("")
def get_dashboard(db: DbSession, org: CurrentOrg, company_id: uuid.UUID | None = None):
    return build_dashboard(db, org.id, company_id)


# ------------------------------ Auditoria -----------------------------------
audit_router = APIRouter(prefix="/audit-logs", tags=["Auditoria"])


@audit_router.get("", response_model=Page[AuditLogOut], dependencies=[require_level(LEVEL_ACCOUNTANT)])
def list_audit_logs(
    db: DbSession, org: CurrentOrg, params: PageDep,
    user_id: uuid.UUID | None = None, action: str | None = None, entity_type: str | None = None,
    date_from: datetime | None = None, date_to: datetime | None = None,
):
    query = select(AuditLog).where(AuditLog.organization_id == org.id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    return paginate(db, query.order_by(AuditLog.created_at.desc()), params)


# ------------------------------ API keys (fase 5) ---------------------------
apikeys_router = APIRouter(prefix="/api-keys", tags=["Integrações"])


@apikeys_router.get("", response_model=list[ApiKeyOut], dependencies=[require_level(LEVEL_OWNER)])
def list_api_keys(db: DbSession, org: CurrentOrg):
    return db.scalars(
        select(ApiKey).where(ApiKey.organization_id == org.id).order_by(ApiKey.created_at.desc())
    ).all()


@apikeys_router.post("", response_model=ApiKeyCreatedOut, status_code=201, dependencies=[require_level(LEVEL_OWNER)])
def create_api_key(payload: ApiKeyCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    secret, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        organization_id=org.id, company_id=payload.company_id, name=payload.name,
        prefix=prefix, key_hash=key_hash, rate_limit_per_minute=payload.rate_limit_per_minute,
    )
    db.add(api_key)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="api_key.create",
          entity_type="api_key", entity_id=api_key.id, request=request)
    db.commit()
    db.refresh(api_key)
    return {"api_key": api_key, "secret": secret}  # segredo exibido uma única vez


@apikeys_router.delete("/{key_id}", status_code=204, dependencies=[require_level(LEVEL_OWNER)])
def revoke_api_key(key_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    api_key = db.get(ApiKey, key_id)
    if api_key is None or api_key.organization_id != org.id:
        raise HTTPException(404, "Chave não encontrada")
    api_key.revoked_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="api_key.revoke",
          entity_type="api_key", entity_id=api_key.id, request=request)
    db.commit()


# ------------------------------ Relatórios ----------------------------------
reports_router = APIRouter(prefix="/reports", tags=["Relatórios"])


@reports_router.get("", response_model=Page[ReportOut])
def list_reports(db: DbSession, org: CurrentOrg, params: PageDep, company_id: uuid.UUID | None = None):
    query = select(Report).where(Report.organization_id == org.id)
    if company_id:
        query = query.where(Report.company_id == company_id)
    return paginate(db, query.order_by(Report.created_at.desc()), params)


# ------------------------------ IA assistente (fase 4) ----------------------
ai_router = APIRouter(prefix="/ai", tags=["IA assistente"])


@ai_router.post("/chat", response_model=ChatResponse, dependencies=[require_level(LEVEL_CONSULTANT)])
def chat(payload: ChatRequest, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    answer, model = ai_assistant.answer_question(db, org, payload.company_id, payload.message)
    if payload.conversation_id:
        conversation = db.get(AIConversation, payload.conversation_id)
        if conversation is None or conversation.organization_id != org.id:
            raise HTTPException(404, "Conversa não encontrada")
    else:
        conversation = AIConversation(
            organization_id=org.id, user_id=user.id,
            title=payload.message[:80], messages=[],
        )
        db.add(conversation)
        db.flush()
    conversation.messages = list(conversation.messages) + [
        {"role": "user", "content": payload.message},
        {"role": "assistant", "content": answer},
    ]
    conversation.model = model
    conversation.last_message_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="ai.chat",
          entity_type="ai_conversation", entity_id=conversation.id, request=request)
    db.commit()
    return ChatResponse(
        conversation_id=conversation.id, answer=answer,
        disclaimer=ai_assistant.DISCLAIMER, model=model,
    )


@ai_router.get("/conversations")
def list_conversations(db: DbSession, org: CurrentOrg, user: CurrentUser):
    conversations = db.scalars(
        select(AIConversation).where(
            AIConversation.organization_id == org.id,
            AIConversation.user_id == user.id,
            AIConversation.deleted_at.is_(None),
        ).order_by(AIConversation.last_message_at.desc())
    ).all()
    return [
        {"id": str(c.id), "title": c.title, "messages": c.messages, "last_message_at": c.last_message_at}
        for c in conversations
    ]
