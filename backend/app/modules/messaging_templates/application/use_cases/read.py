import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination.params import Page, PageParams
from app.modules.messaging_templates.application.authz import assert_can_access
from app.modules.messaging_templates.application.dtos.filters import (
    MessagingTemplateFilters,
)
from app.modules.messaging_templates.application.ports.unit_of_work import (
    MessagingTemplatesUnitOfWorkProtocol,
)
from app.modules.messaging_templates.domain.entities import (
    LinkedService,
    MessagingTemplate,
    MessagingTemplateDetail,
)


class MessagingTemplatesReader:
    def __init__(self, uow: MessagingTemplatesUnitOfWorkProtocol) -> None:
        """
        Inicializa um leitor de templates de mensagem.

        Args:
            uow (MessagingTemplatesUnitOfWorkProtocol):
                Unit of work de templates de mensagem.
        """

        self._uow = uow

    async def get_by_id(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplateDetail:
        """
        Obtém um template de mensagem pelo seu id, incluindo os serviços vinculados.

        Args:
            template_id (uuid.UUID):
                Id do template.
            actor (UserActor):
                Usuário que está executando a ação.
            establishment_id (uuid.UUID):
                Estabelecimento ao qual o template deve pertencer.

        Raises:
            NotFoundError:
                Se o template não existir ou pertencer a outro estabelecimento.
        """

        assert_can_access(actor, establishment_id)
        async with self._uow as uow:
            template = await uow.messaging_templates.get_by_id(template_id)
            self._assert_scope(template, establishment_id)

            links = await uow.messaging_templates.list_services_for_template(
                template_id
            )
            services: list[LinkedService] = []
            for link in links:
                service = await uow.services.get_by_id(link.service_id)
                services.append(LinkedService(id=service.id, name=service.name))

            return MessagingTemplateDetail(
                template=template,
                services=tuple(services),
            )

    async def paginate(
        self,
        page_params: PageParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: MessagingTemplateFilters | None = None,
    ) -> Page[MessagingTemplate]:
        """
        Pagina templates de mensagem do estabelecimento, com filtros opcionais.

        Args:
            page_params (PageParams):
                Parâmetros de paginação.
            actor (UserActor):
                Usuário que está executando a ação.
            establishment_id (uuid.UUID):
                Estabelecimento ao qual os templates devem pertencer.
            filters (MessagingTemplateFilters):
                Filtros adicionais a serem aplicados.
        """

        assert_can_access(actor, establishment_id)
        filters = filters or MessagingTemplateFilters()
        scoped = MessagingTemplateFilters(
            establishment_id=establishment_id,
            is_active=filters.is_active,
            service_id=filters.service_id,
            q=filters.q,
        )
        async with self._uow as uow:
            return await uow.messaging_templates.paginate(
                page_params=page_params,
                filters=scoped,
            )

    def _assert_scope(
        self,
        template: MessagingTemplate,
        establishment_id: uuid.UUID,
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
