from datetime import datetime

from app.modules.memberships.adapters.http.schemas import MembershipRead
from app.modules.users.adapters.http.schemas import UserRead


class UserReadExpanded(UserRead):
    is_global_admin: bool
    created_at: datetime
    updated_at: datetime
    memberships: list[MembershipRead]
