import uuid
from typing import Any

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.messaging_templates.adapters.db.models import (
    MessagingTemplate as MessagingTemplateModel,
)
from app.modules.messaging_templates.adapters.db.models import (
    ServiceMessagingTemplate as ServiceMessagingTemplateModel,
)
from app.modules.messaging_templates.application.dtos.filters import (
    MessagingTemplateFilters,
)
from app.modules.messaging_templates.domain.entities import (
    MessagingTemplate,
    ServiceMessagingTemplate,
)


class MessagingTemplatesRepository(
    BaseRepository[MessagingTemplateModel, MessagingTemplate, MessagingTemplateFilters]
):
    model = MessagingTemplateModel
    filters_type = MessagingTemplateFilters

    async def get_by_id_or_none(self, id_: uuid.UUID) -> MessagingTemplate | None:
        """
        Obtém um template pelo seu id, ignorando templates removidos (soft delete).
        """

        result = await self._session.execute(
            sa.select(self.model).where(
                self.model.id == id_,
                self.model.deleted_at.is_(None),
            )
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None

    async def add_service_link(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
        template_type: str,
    ) -> ServiceMessagingTemplate:
        """Cria o vínculo entre um serviço e um template de mensagem."""

        link = ServiceMessagingTemplateModel(
            template_id=template_id,
            service_id=service_id,
            template_type=template_type,
        )
        self._session.add(link)
        await self._session.flush()
        await self._session.refresh(link)
        return self._to_link_entity(link)

    async def remove_service_link(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
    ) -> None:
        """Remove o vínculo entre um serviço e um template de mensagem, se existir."""

        result = await self._session.execute(
            sa.select(ServiceMessagingTemplateModel).where(
                ServiceMessagingTemplateModel.template_id == template_id,
                ServiceMessagingTemplateModel.service_id == service_id,
            )
        )
        link = result.scalar_one_or_none()
        if link is not None:
            await self._session.delete(link)
            await self._session.flush()

    async def list_services_for_template(
        self,
        template_id: uuid.UUID,
    ) -> list[ServiceMessagingTemplate]:
        """Lista os vínculos de serviço de um template de mensagem."""

        result = await self._session.execute(
            sa.select(ServiceMessagingTemplateModel).where(
                ServiceMessagingTemplateModel.template_id == template_id
            )
        )
        return [self._to_link_entity(row) for row in result.scalars().all()]

    async def get_link_or_none(
        self,
        template_id: uuid.UUID,
        service_id: uuid.UUID,
    ) -> ServiceMessagingTemplate | None:
        """Obtém o vínculo entre um serviço e um template, se existir."""

        result = await self._session.execute(
            sa.select(ServiceMessagingTemplateModel).where(
                ServiceMessagingTemplateModel.template_id == template_id,
                ServiceMessagingTemplateModel.service_id == service_id,
            )
        )
        row = result.scalar_one_or_none()
        return self._to_link_entity(row) if row else None

    async def get_active_templates_for_service(
        self,
        service_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> list[MessagingTemplate]:
        """
        Lista os templates ativos, não removidos e com `minutes_before` definido,
        vinculados a um serviço de um estabelecimento. Usado para agendar as
        notificações de um agendamento.
        """

        query = (
            sa.select(self.model)
            .join(
                ServiceMessagingTemplateModel,
                ServiceMessagingTemplateModel.template_id == self.model.id,
            )
            .where(ServiceMessagingTemplateModel.service_id == service_id)
            .where(self.model.establishment_id == establishment_id)
            .where(self.model.is_active.is_(True))
            .where(self.model.deleted_at.is_(None))
            .where(self.model.minutes_before.is_not(None))
        )
        result = await self._session.execute(query)
        return [self._to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, row: MessagingTemplateModel) -> MessagingTemplate:
        return MessagingTemplate(
            id=row.id,
            establishment_id=row.establishment_id,
            name=row.name,
            content=row.content,
            type=row.type,
            is_active=row.is_active,
            minutes_before=row.minutes_before,
            deleted_at=row.deleted_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_link_entity(
        self, row: ServiceMessagingTemplateModel
    ) -> ServiceMessagingTemplate:
        return ServiceMessagingTemplate(
            id=row.id,
            service_id=row.service_id,
            template_id=row.template_id,
            template_type=row.template_type,
            created_at=row.created_at,
        )

    def _apply_filters(
        self,
        stmt: sa.Select[Any],
        filters: MessagingTemplateFilters,
    ) -> sa.Select[Any]:
        stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters.establishment_id is not None:
            stmt = stmt.where(self.model.establishment_id == filters.establishment_id)
        if filters.is_active is not None:
            stmt = stmt.where(self.model.is_active == filters.is_active)
        if filters.service_id is not None:
            subq = sa.select(ServiceMessagingTemplateModel.template_id).where(
                ServiceMessagingTemplateModel.service_id == filters.service_id
            )
            stmt = stmt.where(self.model.id.in_(subq))
        if filters.q is not None:
            stmt = stmt.where(self.model.name.ilike(f"%{filters.q}%"))
        return stmt
