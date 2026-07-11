import uuid
from dataclasses import dataclass
from typing import Any

from app.core.roles import UserRole
from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewMembership(BaseCreateCommand):
    """Comando de domínio para criação de uma membership."""

    user_id: uuid.UUID
    establishment_id: uuid.UUID
    role: UserRole
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateMembership(BaseUpdateCommand):
    """Comando de domínio para atualização parcial de uma membership."""

    role: UserRole | Unset = UNSET
    is_active: bool | Unset = UNSET


@dataclass(frozen=True, slots=True)
class MembershipUser:
    """Projeção mínima do usuário vinculado a uma membership."""

    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    is_active: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "is_active": self.is_active,
        }


@dataclass(frozen=True, slots=True)
class Membership:
    """Vínculo entre um usuário e um estabelecimento."""

    id: uuid.UUID
    user_id: uuid.UUID
    establishment_id: uuid.UUID
    role: UserRole
    is_active: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "establishment_id": self.establishment_id,
            "role": self.role,
            "is_active": self.is_active,
        }


@dataclass(frozen=True, slots=True)
class MembershipWithUser:
    """Membership com o usuário vinculado embutido, para respostas HTTP."""

    id: uuid.UUID
    establishment_id: uuid.UUID
    role: UserRole
    is_active: bool
    user: MembershipUser

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user": self.user.to_dict(),
            "establishment_id": self.establishment_id,
            "role": self.role,
            "is_active": self.is_active,
        }


@dataclass(frozen=True, slots=True)
class MembershipExpanded:
    """Membership com usuário e estabelecimento completos embutidos."""

    role: UserRole
    is_active: bool
    user: MembershipUser
    establishment: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "is_active": self.is_active,
            "user": self.user.to_dict(),
            "establishment": self.establishment,
        }
