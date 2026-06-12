import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import Company, Organization, User

bearer_scheme = HTTPBearer(auto_error=False)

# Níveis RBAC (ver docs/04-regras-de-negocio.md)
LEVEL_ADMIN = 100
LEVEL_OWNER = 90
LEVEL_ACCOUNTANT = 70
LEVEL_FISCAL = 60
LEVEL_FINANCE = 50
LEVEL_CONSULTANT = 40
LEVEL_READER = 10


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Não autenticado")
    payload = decode_token(credentials.credentials, expected_type="access")
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or user.deleted_at is not None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo ou inexistente")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


def get_organization(user: CurrentUser, db: DbSession) -> Organization:
    org = db.get(Organization, user.organization_id)
    if org is None or org.deleted_at is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organização indisponível")
    return org


CurrentOrg = Annotated[Organization, Depends(get_organization)]


def require_level(min_level: int):
    """Dependency factory de RBAC: exige nível mínimo do perfil do usuário."""

    def checker(user: CurrentUser) -> User:
        if user.role.level < min_level:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permissão insuficiente para esta ação")
        return user

    return Depends(checker)


def get_company_or_404(db: Session, organization_id: uuid.UUID, company_id: uuid.UUID) -> Company:
    """Carrega empresa garantindo isolamento do tenant (org do token, nunca do payload)."""
    company = db.get(Company, company_id)
    if company is None or company.deleted_at is not None or company.organization_id != organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa não encontrada")
    return company
