import uuid
from dataclasses import dataclass


@dataclass
class MessagingTemplateFilters:
    establishment_id: uuid.UUID | None = None
    is_active: bool | None = None
    service_id: uuid.UUID | None = None
    q: str | None = None
