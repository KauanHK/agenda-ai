import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.roles import UserRole
from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewUser(BaseCreateCommand):
    """Comando de domínio para criação de um usuário."""

    name: str
    email: str
    password_hash: str
    phone: str | None = None
    is_global_admin: bool = False
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateUser(BaseUpdateCommand):
    """Comando de domínio para atualização parcial de um usuário."""

    name: str | Unset = UNSET
    email: str | Unset = UNSET
    phone: str | None | Unset = UNSET
    password_hash: str | Unset = UNSET
    is_global_admin: bool | Unset = UNSET
    is_active: bool | Unset = UNSET


@dataclass(frozen=True, slots=True)
class UserMembership:
    """Vínculo de um usuário com um estabelecimento, usado na leitura expandida."""

    id: uuid.UUID
    establishment_id: uuid.UUID
    role: UserRole
    is_active: bool


@dataclass(frozen=True, slots=True)
class User:
    """Usuário do sistema."""

    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    password_hash: str
    is_global_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "is_active": self.is_active,
        }


@dataclass(frozen=True, slots=True)
class UserExpanded:
    """Usuário com dados completos e memberships aninhadas."""

    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    is_active: bool
    is_global_admin: bool
    created_at: datetime
    updated_at: datetime
    memberships: list[UserMembership] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        user_ref = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "is_active": self.is_active,
        }
        return {
            **user_ref,
            "is_global_admin": self.is_global_admin,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "memberships": [
                {
                    "id": m.id,
                    "user": user_ref,
                    "establishment_id": m.establishment_id,
                    "role": m.role,
                    "is_active": m.is_active,
                }
                for m in self.memberships
            ],
        }
