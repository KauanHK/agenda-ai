from dataclasses import dataclass

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset
from app.modules.establishments.domain.enums import DocumentType


@dataclass(frozen=True, slots=True)
class CreateEstablishmentCommand(BaseCreateCommand):
    name: str
    document: str
    document_type: DocumentType
    is_active: bool
    timezone: str
    street: str
    number: str
    complement: str | None
    neighborhood: str
    city: str
    state: str
    zip_code: str


@dataclass(frozen=True, slots=True)
class UpdateEstablishmentCommand(BaseUpdateCommand):
    name: str | Unset = UNSET
    document: str | Unset = UNSET
    timezone: str | Unset = UNSET
    street: str | Unset = UNSET
    number: str | Unset = UNSET
    complement: str | Unset = UNSET
    neighborhood: str | Unset = UNSET
    city: str | Unset = UNSET
    state: str | Unset = UNSET
    zip_code: str | Unset = UNSET
