import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.messaging_templates.application.authz import assert_can_write
from app.modules.messaging_templates.application.ports.unit_of_work import (
    MessagingTemplatesUnitOfWorkProtocol,
)
from app.modules.messaging_templates.domain.entities import (
    MessagingTemplate,
    UpdateMessagingTemplate,
)


class MessagingTemplatesActivator:
    def __init__(self, uow: MessagingTemplatesUnitOfWorkProtocol) -> None:
        """
        Inicializa um ativador de templates de mensagem.

        Args:
            uow (MessagingTemplatesUnitOfWorkProtocol):
                Unit of work de templates de mensagem.
        """

        self._uow = uow

    async def activate(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplate:
        """Ativa um template de mensagem."""

        return await self._set_active(
            template_id,
            is_active=True,
            actor=actor,
            establishment_id=establishment_id,
        )

    async def deactivate(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplate:
        """Desativa um template de mensagem."""

        return await self._set_active(
            template_id,
            is_active=False,
            actor=actor,
            establishment_id=establishment_id,
        )

    async def _set_active(
        self,
        template_id: uuid.UUID,
        is_active: bool,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplate:
        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            template = await uow.messaging_templates.get_by_id(template_id)
            self._assert_scope(template, establishment_id)
            return await uow.messaging_templates.update(
                id_=template_id,
                update_command=UpdateMessagingTemplate(is_active=is_active),
            )

    def _assert_scope(
        self,
        template: MessagingTemplate,
        establishment_id: uuid.UUID,
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
