import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination.params import PageParams
from app.modules.unavailabilities.adapters.db.models import (
    Unavailability as UnavailabilityModel,
)
from app.modules.unavailabilities.adapters.db.repository import (
    UnavailabilitiesRepository,
)
from app.modules.unavailabilities.application.dtos.filters import (
    UnavailabilityFilters,
)
from app.modules.unavailabilities.domain.entities import Unavailability


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> UnavailabilitiesRepository:
    return UnavailabilitiesRepository(session=session)


@pytest.fixture
def model_row() -> UnavailabilityModel:
    now = datetime.now(UTC)
    return UnavailabilityModel(
        id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
        starts_at=now,
        ends_at=now,
        reason="Feriado",
        created_at=now,
        updated_at=now,
    )


async def test_get_by_id_or_none_returns_entity(repo, session, model_row):
    session.get.return_value = model_row

    result = await repo.get_by_id_or_none(model_row.id)

    assert isinstance(result, Unavailability)
    assert result.id == model_row.id
    assert result.reason == "Feriado"


async def test_get_by_id_raises_not_found(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError):
        await repo.get_by_id(uuid.uuid7())


async def test_list_all_applies_filters(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    await repo.list_all(
        UnavailabilityFilters(
            establishment_id=uuid.uuid7(),
            starts_at_from=datetime.now(UTC),
            starts_at_to=datetime.now(UTC),
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
