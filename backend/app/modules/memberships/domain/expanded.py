from app.modules.common.domain.schemas import BaseSchema
from app.modules.establishments.domain.schemas import EstablishmentRead
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.schemas import UserRead


class MembershipReadExpanded(BaseSchema):
    role: UserRole
    is_active: bool
    user: UserRead
    establishment: EstablishmentRead
