import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.messaging_templates.application.authz import assert_can_write
from app.modules.messaging_templates.application.ports.unit_of_work import (
    MessagingTemplatesUnitOfWorkProtocol,
)
from app.modules.messaging_templates.domain.entities import ServiceMessagingTemplate


class MessagingTemplatesServiceLinker:
    def __init__(self, uow: MessagingTemplatesUnitOfWorkProtocol) -> None:
        """
        Inicializa um vinculador de serviços a templates de mensagem.

        Args:
            uow (MessagingTemplatesUnitOfWorkProtocol):
                Unit of work de templates de mensagem.
        """

        self._uow = uow

    async def link(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceMessagingTemplate:
        """
        Vincula um serviço a um template de mensagem.

        Raises:
            NotFoundError:
                Se o template ou o serviço não existirem ou pertencerem a outro
                estabelecimento.
            ConflictError:
                Se o serviço já possuir um template vinculado do mesmo tipo.
        """

        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            template = await uow.messaging_templates.get_by_id(template_id)
            if template.establishment_id != establishment_id:
                raise NotFoundError("Template não encontrado.")

            service = await uow.services.get_by_id(service_id)
            if service.establishment_id != establishment_id:
                raise NotFoundError("Serviço não encontrado.")

            try:
                return await uow.messaging_templates.add_service_link(
                    template_id, service_id, template.type
                )
            except IntegrityError as e:
                raise ConflictError(
                    f"Este serviço já possui um template do tipo '{template.type}'."
                ) from e

    async def unlink(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        """
        Remove o vínculo entre um serviço e um template de mensagem.

        Raises:
            NotFoundError:
                Se o template, o serviço ou o vínculo não existirem.
        """

        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            template = await uow.messaging_templates.get_by_id(template_id)
            if template.establishment_id != establishment_id:
                raise NotFoundError("Template não encontrado.")

            service = await uow.services.get_by_id(service_id)
            if service.establishment_id != establishment_id:
                raise NotFoundError("Serviço não encontrado.")

            link = await uow.messaging_templates.get_link_or_none(
                template_id, service_id
            )
            if link is None:
                raise NotFoundError("Vínculo não encontrado.")

            await uow.messaging_templates.remove_service_link(template_id, service_id)
