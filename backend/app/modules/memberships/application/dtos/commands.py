import uuid
from dataclasses import dataclass

from app.core.roles import UserRole
from app.core.types import UNSET, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class InviteExistingMemberCommand:
    """Comando de aplicação para vincular um usuário já existente a um
    estabelecimento."""

    user_id: uuid.UUID
    role: UserRole


@dataclass(frozen=True, slots=True)
class InviteNewMemberCommand:
    """Comando de aplicação para criar um usuário novo e vinculá-lo a um
    estabelecimento."""

    name: str
    email: str
    password: str
    role: UserRole
    phone: str | None = None


InviteMemberCommand = InviteExistingMemberCommand | InviteNewMemberCommand


@dataclass(frozen=True, slots=True)
class UpdateMembershipCommand(BaseUpdateCommand):
    """Comando de aplicação para atualização parcial de uma membership."""

    role: UserRole | Unset = UNSET
