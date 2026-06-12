import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.org import OrganizationOut


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    lgpd_consent: bool = Field(description="Aceite obrigatório da política de privacidade (LGPD)")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    level: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    is_active: bool
    last_login_at: datetime | None
    role: RoleOut


class MeOut(BaseModel):
    user: UserOut
    organization: OrganizationOut


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    role_slug: str


class UserCreatedOut(BaseModel):
    user: UserOut
    temporary_password: str  # exibida uma única vez


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    role_slug: str | None = None
    is_active: bool | None = None
