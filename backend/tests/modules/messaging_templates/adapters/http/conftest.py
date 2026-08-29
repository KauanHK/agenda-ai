import uuid
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import Membership, UserActor
from app.core.handlers import register_exception_handlers
from app.core.roles import UserRole
from app.modules.messaging_templates.adapters.db.factories import make_unit_of_work
from app.modules.messaging_templates.adapters.http.router import (
    router as messaging_templates_router,
)
from app.modules.messaging_templates.domain.entities import MessagingTemplate
from tests.modules.messaging_templates.application.use_cases.conftest import (
    make_template,
)


class FakeMessagingTemplatesUnitOfWork:
    """Fake da UoW usada nos testes de HTTP, sobrepondo `make_unit_of_work`."""

    def __init__(self, messaging_templates: AsyncMock, services: AsyncMock) -> None:
        self.messaging_templates = messaging_templates
        self.services = services

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(
        messaging_templates_router,
        prefix="/establishments/{establishment_id}/messaging-templates",
    )
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def template_entity(establishment_id) -> MessagingTemplate:
    return make_template(establishment_id)


@pytest.fixture
def templates_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def services_query() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def fake_uow(
    templates_repo: AsyncMock, services_query: AsyncMock
) -> FakeMessagingTemplatesUnitOfWork:
    return FakeMessagingTemplatesUnitOfWork(
        messaging_templates=templates_repo, services=services_query
    )


@pytest.fixture
def mock_actor(establishment_id) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=False,
        memberships=(
            Membership(
                establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
            ),
        ),
    )


@pytest.fixture(autouse=True)
def override_dependencies(
    app: FastAPI,
    fake_uow: FakeMessagingTemplatesUnitOfWork,
    mock_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_actor

    app.dependency_overrides[make_unit_of_work] = lambda: fake_uow
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
