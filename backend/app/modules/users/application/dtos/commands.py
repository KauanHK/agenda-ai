import uuid
from dataclasses import dataclass

from app.core.roles import UserRole
from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateUserCommand(BaseCreateCommand):
    """Comando de aplicação para criação de um usuário."""

    name: str
    email: str
    password: str
    role: UserRole = UserRole.MEMBER
    establishment_id: uuid.UUID | None = None
    phone: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateUserCommand(BaseUpdateCommand):
    """Comando de aplicação para atualização parcial de um usuário."""

    name: str | Unset = UNSET
    email: str | Unset = UNSET
    phone: str | None | Unset = UNSET
