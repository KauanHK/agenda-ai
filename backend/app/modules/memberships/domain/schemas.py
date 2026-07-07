from pydantic import UUID7, EmailStr

from app.modules.clients.domain.schemas import Phone
from app.modules.common.domain.schemas import BaseSchema
from app.modules.establishments.domain.schemas import Name
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.schemas import Password, UserRead


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
