from datetime import time

import pytest

from app.core.exceptions import ForbiddenError
from app.modules.operating_hours.application.update import OperatingHoursUpdater
from app.modules.operating_hours.domain.model import OperatingHour
from app.modules.operating_hours.domain.schemas import OperatingHourRead, OperatingHoursUpdate
from tests.modules.operating_hours.application.conftest import make_actor


@pytest.fixture
def updater(mock_uow) -> OperatingHoursUpdater:
    return OperatingHoursUpdater(uow=mock_uow)


@pytest.fixture
def payload() -> OperatingHoursUpdate:
    return OperatingHoursUpdate(
        items=[
            {"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"},
            {"weekday": 1, "start_time": "09:00:00", "end_time": "18:00:00"},
        ]
    )


async def test_update_returns_list_of_operating_hour_read(
    updater, admin_user, establishment_id, payload
):
    result = await updater.update(payload, admin_user, establishment_id)

    assert isinstance(result, list)
    assert all(isinstance(h, OperatingHourRead) for h in result)


async def test_update_calls_replace_all_with_correct_hours(
    updater, mock_repo, admin_user, establishment_id, payload
):
    await updater.update(payload, admin_user, establishment_id)

    mock_repo.replace_all.assert_awaited_once()
    _, hours = mock_repo.replace_all.call_args[0]
    assert all(isinstance(h, OperatingHour) for h in hours)
    assert all(h.establishment_id == establishment_id for h in hours)
    assert {h.weekday for h in hours} == {0, 1}


async def test_update_forbidden_for_member(updater, member_user, establishment_id, payload):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await updater.update(payload, member_user, establishment_id)


async def test_update_forbidden_for_global_admin(
    updater, global_admin_user, establishment_id, payload
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await updater.update(payload, global_admin_user, establishment_id)


async def test_update_forbidden_when_not_member(updater, establishment_id, payload):
    actor = make_actor()

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await updater.update(payload, actor, establishment_id)
