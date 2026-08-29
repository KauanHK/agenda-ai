import uuid
from datetime import UTC, datetime
from types import SimpleNamespace, TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import Membership, UserActor
from app.core.roles import UserRole
from app.modules.messaging_templates.domain.entities import (
    MessagingTemplate,
    ServiceMessagingTemplate,
)
from app.modules.messaging_templates.domain.enums import TemplateType


class FakeMessagingTemplatesUnitOfWork:
    """Fake de `MessagingTemplatesUnitOfWorkProtocol` para testar os use cases isoladamente."""

    def __init__(self, messaging_templates: AsyncMock, services: AsyncMock) -> None:
        self.messaging_templates = messaging_templates
        self.services = services
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exited = True
        return None


def make_actor(
    is_global_admin: bool = False,
    establishment_id: uuid.UUID | None = None,
    role: str | None = None,
) -> UserActor:
    memberships: tuple[Membership, ...] = ()
    if establishment_id is not None and role is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=memberships
    )


def make_template(establishment_id: uuid.UUID, **overrides) -> MessagingTemplate:
    now = datetime.now(UTC)
    defaults = dict(  # noqa: C408
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name="Lembrete padrão",
        content="Olá {cliente}, seu horário é {data}.",
        type=TemplateType.REMINDER,
        is_active=True,
        minutes_before=60,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return MessagingTemplate(**defaults)


def make_link(
    template_id: uuid.UUID,
    service_id: uuid.UUID,
    template_type: TemplateType = TemplateType.REMINDER,
) -> ServiceMessagingTemplate:
    return ServiceMessagingTemplate(
        id=uuid.uuid7(),
        service_id=service_id,
        template_id=template_id,
        template_type=template_type,
        created_at=datetime.now(UTC),
    )


def make_service(
    establishment_id: uuid.UUID, name: str = "Corte de cabelo"
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name=name,
    )


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def templates_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def services_query() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(
    templates_repo: AsyncMock, services_query: AsyncMock
) -> FakeMessagingTemplatesUnitOfWork:
    return FakeMessagingTemplatesUnitOfWork(
        messaging_templates=templates_repo, services=services_query
    )


@pytest.fixture
def template(establishment_id) -> MessagingTemplate:
    return make_template(establishment_id)


@pytest.fixture
def admin_user(establishment_id) -> UserActor:
    return make_actor(
        establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
    )


@pytest.fixture
def member_user(establishment_id) -> UserActor:
    return make_actor(establishment_id=establishment_id, role=UserRole.MEMBER)


@pytest.fixture
def global_admin_user() -> UserActor:
    return make_actor(is_global_admin=True)
