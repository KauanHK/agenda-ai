import uuid
from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.modules.messaging_templates.application.dtos.filters import (
    MessagingTemplateFilters,
)
from app.modules.messaging_templates.domain.entities import (
    MessagingTemplate,
    NewMessagingTemplate,
    ServiceMessagingTemplate,
    UpdateMessagingTemplate,
)
from app.modules.services.domain.model import Service


class MessagingTemplatesRepositoryProtocol(
    BaseRepositoryProtocol[
        MessagingTemplate,
        MessagingTemplateFilters,
        NewMessagingTemplate,
        UpdateMessagingTemplate,
    ],
    Protocol,
):
    async def add_service_link(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
        template_type: str,
    ) -> ServiceMessagingTemplate: ...

    async def remove_service_link(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
    ) -> None: ...

    async def list_services_for_template(
        self,
        template_id: uuid.UUID,
    ) -> list[ServiceMessagingTemplate]: ...

    async def get_link_or_none(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
    ) -> ServiceMessagingTemplate | None: ...

    async def get_active_templates_for_service(
        self,
        service_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> list[MessagingTemplate]: ...


class ServicesQueryProtocol(Protocol):
    """
    Consulta mínima de serviços usada para validar vínculos de templates de
    mensagem. `services` pertence a outro módulo; este protocolo isola apenas o que
    é necessário aqui.
    """

    async def get_by_id(self, service_id: uuid.UUID) -> Service: ...
