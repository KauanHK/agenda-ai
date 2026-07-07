import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.application._authz import assert_can_write
from app.modules.messaging_templates.domain.schemas import ServiceMessagingTemplateRead
from app.modules.messaging_templates.infra.repository import (
    MessagingTemplatesRepository,
)
from app.modules.services.infra.repository import ServicesRepository


class MessagingTemplatesServiceLinker:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def link(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceMessagingTemplateRead:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)
            services_repo = self._uow.repository(ServicesRepository)

            template = await repo.get_by_id(template_id)
            if template.establishment_id != establishment_id:
                raise NotFoundError("Template não encontrado.")

            service = await services_repo.get_by_id(service_id)
            if service.establishment_id != establishment_id:
                raise NotFoundError("Serviço não encontrado.")

            try:
                link = await repo.add_service_link(
                    template_id, service_id, template.type
                )
            except IntegrityError as e:
                raise ConflictError(
                    f"Este serviço já possui um template do tipo '{template.type}'."
                ) from e

            return ServiceMessagingTemplateRead.model_validate(link)

    async def unlink(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)
            services_repo = self._uow.repository(ServicesRepository)

            template = await repo.get_by_id(template_id)
            if template.establishment_id != establishment_id:
                raise NotFoundError("Template não encontrado.")

            service = await services_repo.get_by_id(service_id)
            if service.establishment_id != establishment_id:
                raise NotFoundError("Serviço não encontrado.")

            link = await repo.get_link_or_none(template_id, service_id)
            if link is None:
                raise NotFoundError("Vínculo não encontrado.")

            await repo.remove_service_link(template_id, service_id)
