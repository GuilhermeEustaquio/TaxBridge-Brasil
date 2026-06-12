import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog, User


def audit(
    db: Session,
    *,
    organization_id: uuid.UUID,
    action: str,
    user: User | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    metadata: dict | None = None,
    request: Request | None = None,
) -> None:
    """Registra trilha de auditoria (LGPD): quem, o quê, quando, de onde.

    Nunca incluir senha/segredos em `metadata`. O commit fica a cargo do endpoint
    para que a auditoria entre na mesma transação da ação auditada.
    """
    ip = None
    user_agent = None
    if request is not None:
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
        user_agent = (request.headers.get("user-agent") or "")[:255] or None

    db.add(
        AuditLog(
            organization_id=organization_id,
            user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            extra=metadata or {},
            ip_address=ip,
            user_agent=user_agent,
        )
    )
