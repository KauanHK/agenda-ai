from app.core.roles import UserRole
from app.core.schemas import BaseSchema
from app.modules.establishments.domain.schemas import EstablishmentRead
from app.modules.users.adapters.http.schemas import UserRead


class MembershipReadExpanded(BaseSchema):
    role: UserRole
    is_active: bool
    user: UserRead
    establishment: EstablishmentRead
