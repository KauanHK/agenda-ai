import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.messaging_templates.domain.filters import MessagingTemplateFilters
from app.modules.messaging_templates.domain.enums import TemplateType
from app.modules.messaging_templates.domain.model import (
    MessagingTemplate,
    ServiceMessagingTemplate,
)


class MessagingTemplatesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id_or_none(
        self,
        template_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> MessagingTemplate | None:
        query = select(MessagingTemplate).where(MessagingTemplate.id == template_id)
        if not include_deleted:
            query = query.where(MessagingTemplate.deleted_at.is_(None))
        result = await self._session.execute(query)
        return result.scalars().one_or_none()

    async def get_by_id(
        self,
        template_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> MessagingTemplate:
        template = await self.get_by_id_or_none(template_id, include_deleted=include_deleted)
        if template is None:
            raise NotFoundError("Template não encontrado.")
        return template

    async def create(self, template: MessagingTemplate) -> MessagingTemplate:
        self._session.add(template)
        await self._session.flush()
        await self._session.refresh(template)
        return template

    async def update(self, template: MessagingTemplate) -> MessagingTemplate:
        merged = await self._session.merge(template)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def list(
        self,
        pagination: PaginationParams,
        filters: MessagingTemplateFilters | None = None,
        include_deleted: bool = False,
    ) -> list[MessagingTemplate]:
        query = self._construct_select_query(filters, include_deleted=include_deleted)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(
        self,
        filters: MessagingTemplateFilters | None = None,
        include_deleted: bool = False,
    ) -> int:
        query = select(func.count()).select_from(  # pylint: disable=not-callable
            self._construct_select_query(filters, include_deleted=include_deleted).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def add_service_link(
        self, template_id: uuid.UUID, service_id: uuid.UUID, template_type: "TemplateType"
    ) -> ServiceMessagingTemplate:
        link = ServiceMessagingTemplate(
            template_id=template_id, service_id=service_id, template_type=template_type
        )
        self._session.add(link)
        await self._session.flush()
        await self._session.refresh(link)
        return link

    async def remove_service_link(self, template_id: uuid.UUID, service_id: uuid.UUID) -> None:
        link = await self.get_link_or_none(template_id, service_id)
        if link is not None:
            await self._session.delete(link)
            await self._session.flush()

    async def list_services_for_template(self, template_id: uuid.UUID) -> list[ServiceMessagingTemplate]:
        query = select(ServiceMessagingTemplate).where(ServiceMessagingTemplate.template_id == template_id)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def get_link_or_none(
        self, template_id: uuid.UUID, service_id: uuid.UUID
    ) -> ServiceMessagingTemplate | None:
        query = select(ServiceMessagingTemplate).where(
            ServiceMessagingTemplate.template_id == template_id,
            ServiceMessagingTemplate.service_id == service_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_templates_for_service(
        self, service_id: uuid.UUID, establishment_id: uuid.UUID
    ) -> list[MessagingTemplate]:
        query = (
            select(MessagingTemplate)
            .join(ServiceMessagingTemplate, ServiceMessagingTemplate.template_id == MessagingTemplate.id)
            .where(ServiceMessagingTemplate.service_id == service_id)
            .where(MessagingTemplate.establishment_id == establishment_id)
            .where(MessagingTemplate.is_active.is_(True))
            .where(MessagingTemplate.deleted_at.is_(None))
            .where(MessagingTemplate.minutes_before.is_not(None))
        )
        result = await self._session.execute(query)
        return list(result.scalars())

    def _construct_select_query(
        self,
        filters: MessagingTemplateFilters | None = None,
        include_deleted: bool = False,
    ) -> Select[tuple[MessagingTemplate]]:
        query = select(MessagingTemplate)
        if not include_deleted:
            query = query.where(MessagingTemplate.deleted_at.is_(None))
        if filters is None:
            return query
        if filters.establishment_id is not None:
            query = query.where(MessagingTemplate.establishment_id == filters.establishment_id)
        if filters.is_active is not None:
            query = query.where(MessagingTemplate.is_active == filters.is_active)
        if filters.service_id is not None:
            subq = select(ServiceMessagingTemplate.template_id).where(
                ServiceMessagingTemplate.service_id == filters.service_id
            )
            query = query.where(MessagingTemplate.id.in_(subq))
        if filters.q is not None:
            like = f"%{filters.q}%"
            query = query.where(MessagingTemplate.name.ilike(like))
        return query
