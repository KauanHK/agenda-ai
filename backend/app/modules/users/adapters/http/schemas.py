import uuid
from typing import Annotated

from pydantic import UUID7, EmailStr, Field

from app.core.roles import UserRole
from app.core.schemas import BaseSchema

Name = Annotated[str, Field(max_length=255)]
Phone = Annotated[str, Field(max_length=20)]
Password = Annotated[str, Field(min_length=8)]


class UserBase(BaseSchema):
    name: Name
    email: EmailStr
    phone: Phone | None = None


class UserCreate(UserBase):
    password: Password
    role: UserRole = UserRole.MEMBER
    establishment_id: uuid.UUID | None = None


class UserRead(UserBase):
    id: UUID7
    is_active: bool


class UserUpdate(BaseSchema):
    name: Name | None = None
    email: EmailStr | None = None
    phone: Phone | None = None


class ChangePassword(BaseSchema):
    current_password: Password
    password: Password


class UsersFilters(BaseSchema):
    q: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
