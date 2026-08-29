from dataclasses import dataclass

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateClientCommand(BaseCreateCommand):
    name: str
    phone: str
    email: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateClientCommand(BaseUpdateCommand):
    name: str | Unset = UNSET
    phone: str | Unset = UNSET
    email: str | None | Unset = UNSET
    is_active: bool | Unset = UNSET
