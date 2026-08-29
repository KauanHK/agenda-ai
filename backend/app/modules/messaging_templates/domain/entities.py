import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset
from app.modules.messaging_templates.domain.enums import TemplateType


@dataclass(frozen=True, slots=True)
class NewMessagingTemplate(BaseCreateCommand):
    establishment_id: uuid.UUID
    name: str
    content: str
    type: TemplateType
    minutes_before: int | None = None


@dataclass(frozen=True, slots=True)
class UpdateMessagingTemplate(BaseUpdateCommand):
    name: str | Unset = UNSET
    content: str | Unset = UNSET
    type: TemplateType | Unset = UNSET
    minutes_before: int | None | Unset = UNSET
    is_active: bool | Unset = UNSET
    deleted_at: datetime | None | Unset = UNSET


@dataclass(frozen=True, slots=True)
class MessagingTemplate:
    id: uuid.UUID
    establishment_id: uuid.UUID
    name: str
    content: str
    type: TemplateType
    is_active: bool
    minutes_before: int | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "establishment_id": self.establishment_id,
            "name": self.name,
            "content": self.content,
            "type": self.type,
            "is_active": self.is_active,
            "minutes_before": self.minutes_before,
            "deleted_at": self.deleted_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True, slots=True)
class ServiceMessagingTemplate:
    """Vínculo entre um serviço e um template de mensagem para um dado tipo de envio."""

    id: uuid.UUID
    service_id: uuid.UUID
    template_id: uuid.UUID
    template_type: TemplateType
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "service_id": self.service_id,
            "template_id": self.template_id,
            "template_type": self.template_type,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class LinkedService:
    """Projeção mínima de um serviço vinculado, usada na leitura detalhada de um template."""

    id: uuid.UUID
    name: str


@dataclass(frozen=True, slots=True)
class MessagingTemplateDetail:
    """Template de mensagem com os serviços vinculados, para a leitura detalhada."""

    template: MessagingTemplate
    services: tuple[LinkedService, ...]

    def to_dict(self) -> dict[str, Any]:
        data = self.template.to_dict()
        data["services"] = [{"id": s.id, "name": s.name} for s in self.services]
        return data
