from pydantic import UUID7, EmailStr

from app.core.roles import UserRole
from app.core.schemas import BaseSchema
from app.modules.clients.domain.schemas import Phone
from app.modules.establishments.domain.schemas import Name
from app.modules.users.adapters.http.schemas import Password, UserRead


class MembershipUpdate(BaseSchema):
    role: UserRole


class MembershipRead(BaseSchema):
    id: UUID7
    user: UserRead
    establishment_id: UUID7
    role: UserRole
    is_active: bool


class MembershipInviteExisting(BaseSchema):
    user_id: UUID7
    role: UserRole


class MembershipInviteNew(BaseSchema):
    name: Name
    email: EmailStr
    phone: Phone | None = None
    password: Password
    role: UserRole


MembershipInvitePayload = MembershipInviteExisting | MembershipInviteNew
