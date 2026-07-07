import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import Membership, UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.domain.enums import TemplateType
from app.modules.messaging_templates.domain.model import (
    MessagingTemplate,
    ServiceMessagingTemplate,
)
from app.modules.messaging_templates.infra.repository import (
    MessagingTemplatesRepository,
)
from app.modules.services.domain.model import Service
from app.modules.services.infra.repository import ServicesRepository
from app.modules.users.domain.enums import UserRole


def make_template(
    establishment_id: uuid.UUID,
    template_type: TemplateType = TemplateType.CONFIRMATION,
    name: str = "Confirmação Padrão",
    content: str = "Olá {nome}, sua consulta está confirmada.",
    is_active: bool = True,
) -> MessagingTemplate:
    return MessagingTemplate(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name=name,
        content=content,
        type=template_type,
        is_active=is_active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_service(
    establishment_id: uuid.UUID,
    name: str = "Corte de Cabelo",
) -> Service:
    return Service(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name=name,
        duration_minutes=30,
        price=Decimal("50.00"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_link(
    template_id: uuid.UUID,
    service_id: uuid.UUID,
    template_type: TemplateType = TemplateType.CONFIRMATION,
) -> ServiceMessagingTemplate:
    return ServiceMessagingTemplate(
        id=uuid.uuid7(),
        template_id=template_id,
        service_id=service_id,
        template_type=template_type,
        created_at=datetime.now(UTC),
    )


def make_actor(
    is_global_admin: bool = False,
    establishment_id: uuid.UUID | None = None,
    role: str | None = None,
) -> UserActor:
    memberships: tuple[Membership, ...] = ()
    if establishment_id is not None and role is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=is_global_admin,
        memberships=memberships,
    )


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def template_model(establishment_id) -> MessagingTemplate:
    return make_template(establishment_id=establishment_id)


@pytest.fixture
def service_model(establishment_id) -> Service:
    return make_service(establishment_id=establishment_id)


@pytest.fixture
def link_model(template_model, service_model) -> ServiceMessagingTemplate:
    return make_link(
        template_id=template_model.id,
        service_id=service_model.id,
        template_type=template_model.type,
    )


@pytest.fixture
def mock_template_repo(template_model, link_model) -> AsyncMock:
    repo = AsyncMock(spec=MessagingTemplatesRepository)
    repo.get_by_id.return_value = template_model
    repo.create.return_value = template_model
    repo.update.return_value = template_model
    repo.list.return_value = [template_model]
    repo.count.return_value = 1
    repo.list_services_for_template.return_value = []
    repo.add_service_link.return_value = link_model
    repo.get_link_or_none.return_value = link_model
    return repo


@pytest.fixture
def mock_services_repo(service_model) -> AsyncMock:
    repo = AsyncMock(spec=ServicesRepository)
    repo.get_by_id.return_value = service_model
    return repo


@pytest.fixture
def mock_uow(mock_template_repo, mock_services_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None

    def get_repo(cls):
        if cls is MessagingTemplatesRepository:
            return mock_template_repo
        if cls is ServicesRepository:
            return mock_services_repo
        raise ValueError(f"Unexpected repository: {cls}")

    uow.repository.side_effect = get_repo
    return uow


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
