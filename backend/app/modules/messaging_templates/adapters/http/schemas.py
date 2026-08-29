from datetime import datetime
from typing import Annotated

from pydantic import UUID7, Field

from app.core.schemas import BaseSchema
from app.modules.common.domain.schemas import EstablishmentScoped, TimestampMixin
from app.modules.messaging_templates.domain.enums import TemplateType

Name = Annotated[str, Field(min_length=1, max_length=255)]
Content = Annotated[str, Field(min_length=1)]


class ServiceRef(BaseSchema):
    id: UUID7
    name: str


class MessagingTemplateBase(BaseSchema):
    name: Name
    content: Content
    type: TemplateType
    minutes_before: int | None = None


class MessagingTemplateListItem(
    MessagingTemplateBase, EstablishmentScoped, TimestampMixin
):
    id: UUID7
    is_active: bool


class MessagingTemplateRead(MessagingTemplateListItem):
    services: list[ServiceRef] = Field(default_factory=list)


class ServiceMessagingTemplateRead(BaseSchema):
    id: UUID7
    service_id: UUID7
    template_id: UUID7
    template_type: TemplateType
    created_at: datetime


class MessagingTemplateCreate(MessagingTemplateBase):
    pass


class MessagingTemplateUpdate(BaseSchema):
    name: Name | None = None
    content: Content | None = None
    type: TemplateType | None = None
    minutes_before: int | None = None
    is_active: bool | None = None


class MessagingTemplatesPaginationFilters(BaseSchema):
    is_active: bool | None = None
    service_id: UUID7 | None = None
    q: str | None = None
