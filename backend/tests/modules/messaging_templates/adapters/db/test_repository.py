import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination.params import PageParams
from app.modules.messaging_templates.adapters.db.models import (
    MessagingTemplate as MessagingTemplateModel,
)
from app.modules.messaging_templates.adapters.db.repository import (
    MessagingTemplatesRepository,
)
from app.modules.messaging_templates.application.dtos.filters import (
    MessagingTemplateFilters,
)
from app.modules.messaging_templates.domain.entities import MessagingTemplate
from app.modules.messaging_templates.domain.enums import TemplateType


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> MessagingTemplatesRepository:
    return MessagingTemplatesRepository(session=session)


@pytest.fixture
def model_row() -> MessagingTemplateModel:
    now = datetime.now(UTC)
    return MessagingTemplateModel(
        id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
        name="Lembrete padrão",
        content="Olá {cliente}!",
        type=TemplateType.REMINDER,
        is_active=True,
        minutes_before=60,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )


def make_execute_result(row) -> MagicMock:
    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = row
    return result_mock


async def test_get_by_id_or_none_returns_entity(repo, session, model_row):
    session.execute.return_value = make_execute_result(model_row)

    result = await repo.get_by_id_or_none(model_row.id)

    assert isinstance(result, MessagingTemplate)
    assert result.id == model_row.id
    assert result.type == TemplateType.REMINDER


async def test_get_by_id_or_none_returns_none_when_not_found(repo, session):
    session.execute.return_value = make_execute_result(None)

    result = await repo.get_by_id_or_none(uuid.uuid7())

    assert result is None


async def test_get_by_id_raises_not_found(repo, session):
    session.execute.return_value = make_execute_result(None)

    with pytest.raises(NotFoundError):
        await repo.get_by_id(uuid.uuid7())


async def test_list_all_applies_filters(repo, session):
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock

    await repo.list_all(
        MessagingTemplateFilters(
            establishment_id=uuid.uuid7(),
            is_active=True,
            service_id=uuid.uuid7(),
            q="lembrete",
        )
    )

    session.execute.assert_awaited_once()


async def test_paginate_returns_page(repo, session, model_row):
    session.scalar = AsyncMock(return_value=1)

    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = [model_row]
    session.execute.return_value = rows_result

    page = await repo.paginate(PageParams(page=1, page_size=10))

    assert page.total == 1
    assert page.items[0].id == model_row.id
