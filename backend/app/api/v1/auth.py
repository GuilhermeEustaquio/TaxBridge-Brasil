import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.core.audit import audit
from app.core.deps import CurrentOrg, CurrentUser, DbSession
from app.core.rate_limit import auth_rate_limit
from app.core.security import create_token_pair, decode_token, hash_password, verify_password
from app.db.seed import ensure_roles_and_permissions, seed_transition_years
from app.models import Organization, Role, User
from app.schemas.auth import LoginRequest, MeOut, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.org import Assumptions

router = APIRouter(prefix="/auth", tags=["Auth"], dependencies=[Depends(auth_rate_limit)])

LGPD_POLICY_VERSION = "2026-01"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
    return slug or "org"


@router.post("/register", response_model=TokenPair, status_code=201)
def register(payload: RegisterRequest, db: DbSession, request: Request):
    if not payload.lgpd_consent:
        raise HTTPException(422, "É necessário aceitar a política de privacidade (LGPD)")
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(409, "E-mail já cadastrado")

    ensure_roles_and_permissions(db)

    slug = _slugify(payload.organization_name)
    if db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    org = Organization(
        name=payload.organization_name,
        slug=slug,
        assumptions=Assumptions().model_dump(mode="json"),
        lgpd_consent_version=LGPD_POLICY_VERSION,
        lgpd_consent_at=datetime.now(timezone.utc),
    )
    db.add(org)
    db.flush()
    seed_transition_years(db, org.id)

    owner_role = db.scalar(select(Role).where(Role.slug == "dono_conta"))
    user = User(
        organization_id=org.id,
        role_id=owner_role.id,
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="auth.register",
          entity_type="organization", entity_id=org.id, request=request)
    db.commit()
    return create_token_pair(str(user.id), str(org.id), owner_role.slug)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: DbSession, request: Request):
    user = db.scalar(select(User).where(User.email == payload.email.lower(), User.deleted_at.is_(None)))
    # Mensagem neutra: não revelar se o e-mail existe (anti user-enumeration)
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Credenciais inválidas")
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, organization_id=user.organization_id, user=user, action="auth.login", request=request)
    db.commit()
    return create_token_pair(str(user.id), str(user.organization_id), user.role.slug)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession):
    decoded = decode_token(payload.refresh_token, expected_type="refresh")
    if decoded is None:
        raise HTTPException(401, "Refresh token inválido ou expirado")
    user = db.get(User, uuid.UUID(decoded["sub"]))
    if user is None or user.deleted_at is not None or not user.is_active:
        raise HTTPException(401, "Usuário inativo")
    return create_token_pair(str(user.id), str(user.organization_id), user.role.slug)


@router.get("/me", response_model=MeOut)
def me(user: CurrentUser, org: CurrentOrg):
    return {"user": user, "organization": org}


@router.post("/logout", status_code=204)
def logout(user: CurrentUser, db: DbSession, request: Request):
    audit(db, organization_id=user.organization_id, user=user, action="auth.logout", request=request)
    db.commit()
