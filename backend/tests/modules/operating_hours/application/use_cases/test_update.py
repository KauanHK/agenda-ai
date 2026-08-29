from datetime import time

import pytest

from app.core.exceptions import ForbiddenError
from app.modules.operating_hours.application.dtos.commands import (
    OperatingHourItemCommand,
    ReplaceOperatingHoursCommand,
)
from app.modules.operating_hours.application.use_cases.update import (
    OperatingHoursUpdater,
)
from app.modules.operating_hours.domain.entities import NewOperatingHour
from tests.modules.operating_hours.application.use_cases.conftest import (
    make_operating_hour,
)


@pytest.fixture
def payload() -> ReplaceOperatingHoursCommand:
    return ReplaceOperatingHoursCommand(
        items=[
            OperatingHourItemCommand(
                weekday=1, start_time=time(8, 0), end_time=time(18, 0)
            ),
            OperatingHourItemCommand(
                weekday=2, start_time=time(8, 0), end_time=time(12, 0)
            ),
        ]
    )


async def test_update_replaces_all_hours(
    uow, operating_hours_repo, admin_user, establishment_id, payload
):
    hours = [make_operating_hour(establishment_id)]
    operating_hours_repo.replace_all.return_value = hours

    result = await OperatingHoursUpdater(uow).update(
        payload, admin_user, establishment_id
    )

    assert result == hours


async def test_update_scopes_hours_to_establishment(
    uow, operating_hours_repo, admin_user, establishment_id, payload
):
    operating_hours_repo.replace_all.return_value = []

    await OperatingHoursUpdater(uow).update(payload, admin_user, establishment_id)

    operating_hours_repo.replace_all.assert_awaited_once()
    sent_establishment_id, sent_hours = operating_hours_repo.replace_all.call_args[0]
    assert sent_establishment_id == establishment_id
    assert len(sent_hours) == 2
    assert all(isinstance(h, NewOperatingHour) for h in sent_hours)
    assert all(h.establishment_id == establishment_id for h in sent_hours)


async def test_update_forbidden_for_member(uow, member_user, establishment_id, payload):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await OperatingHoursUpdater(uow).update(payload, member_user, establishment_id)


async def test_update_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, payload
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await OperatingHoursUpdater(uow).update(
            payload, global_admin_user, establishment_id
        )
