from datetime import datetime

from app.modules.memberships.domain.schemas import MembershipRead
from app.modules.users.domain.schemas import UserRead


class UserReadExpanded(UserRead):
    is_global_admin: bool
    created_at: datetime
    updated_at: datetime
    memberships: list[MembershipRead]
