from dataclasses import dataclass

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset
from app.modules.messaging_templates.domain.enums import TemplateType


@dataclass(frozen=True, slots=True)
class CreateMessagingTemplateCommand(BaseCreateCommand):
    name: str
    content: str
    type: TemplateType
    minutes_before: int | None = None


@dataclass(frozen=True, slots=True)
class UpdateMessagingTemplateCommand(BaseUpdateCommand):
    name: str | Unset = UNSET
    content: str | Unset = UNSET
    type: TemplateType | Unset = UNSET
    minutes_before: int | None | Unset = UNSET
    is_active: bool | Unset = UNSET
