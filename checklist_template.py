import secrets
import uuid

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.audit import audit
from app.core.deps import LEVEL_OWNER, CurrentOrg, CurrentUser, DbSession, require_level
from app.core.security import hash_password
from app.models import Role, User
from app.schemas.auth import RoleOut, UserCreate, UserCreatedOut, UserOut, UserUpdate

router = APIRouter(tags=["Usuários e perfis"])


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: DbSession, _user: CurrentUser):
    return db.scalars(select(Role).order_by(Role.level.desc())).all()


@router.get("/users", response_model=list[UserOut], dependencies=[require_level(LEVEL_OWNER)])
def list_users(db: DbSession, org: CurrentOrg):
    return db.scalars(
        select(User).where(User.organization_id == org.id, User.deleted_at.is_(None)).order_by(User.name)
    ).all()


@router.post("/users", response_model=UserCreatedOut, status_code=201, dependencies=[require_level(LEVEL_OWNER)])
def invite_user(payload: UserCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(409, "E-mail já cadastrado")
    role = db.scalar(select(Role).where(Role.slug == payload.role_slug))
    if role is None:
        raise HTTPException(422, "Perfil inexistente")
    if role.slug == "admin_global":
        raise HTTPException(403, "Perfil admin_global é reservado")
    temporary_password = secrets.token_urlsafe(10)
    new_user = User(
        organization_id=org.id,
        role_id=role.id,
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(temporary_password),
    )
    db.add(new_user)
    db.flush()
    audit(db, organization_id=org.id, user=user, action="user.invite",
          entity_type="user", entity_id=new_user.id, metadata={"role": role.slug}, request=request)
    db.commit()
    db.refresh(new_user)
    return {"user": new_user, "temporary_password": temporary_password}


@router.put("/users/{user_id}", response_model=UserOut, dependencies=[require_level(LEVEL_OWNER)])
def update_user(user_id: uuid.UUID, payload: UserUpdate, db: DbSession, org: CurrentOrg,
                user: CurrentUser, request: Request):
    target = db.get(User, user_id)
    if target is None or target.organization_id != org.id or target.deleted_at is not None:
        raise HTTPException(404, "Usuário não encontrado")
    changes: list[str] = []
    if payload.name is not None:
        target.name = payload.name
        changes.append("name")
    if payload.is_active is not None:
        if target.id == user.id and not payload.is_active:
            raise HTTPException(422, "Não é possível desativar o próprio usuário")
        target.is_active = payload.is_active
        changes.append("is_active")
    if payload.role_slug is not None:
        role = db.scalar(select(Role).where(Role.slug == payload.role_slug))
        if role is None or role.slug == "admin_global":
            raise HTTPException(422, "Perfil inválido")
        target.role_id = role.id
        changes.append("role")
    audit(db, organization_id=org.id, user=user, action="user.update",
          entity_type="user", entity_id=target.id, metadata={"changes": changes}, request=request)
    db.commit()
    db.refresh(target)
    return target
