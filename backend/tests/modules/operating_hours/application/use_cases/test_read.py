import pytest

from app.core.exceptions import ForbiddenError
from app.modules.operating_hours.application.use_cases.read import (
    OperatingHoursReader,
)
from tests.modules.operating_hours.application.use_cases.conftest import (
    make_actor,
    make_operating_hour,
)


async def test_list_returns_operating_hours(
    uow, operating_hours_repo, admin_user, establishment_id
):
    hour = make_operating_hour(establishment_id)
    operating_hours_repo.list_by_establishment.return_value = [hour]

    result = await OperatingHoursReader(uow).list(admin_user, establishment_id)

    assert result == [hour]
    operating_hours_repo.list_by_establishment.assert_awaited_once_with(
        establishment_id
    )


async def test_list_allowed_for_member(
    uow, operating_hours_repo, member_user, establishment_id
):
    operating_hours_repo.list_by_establishment.return_value = []

    result = await OperatingHoursReader(uow).list(member_user, establishment_id)

    assert result == []


async def test_list_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await OperatingHoursReader(uow).list(global_admin_user, establishment_id)


async def test_list_forbidden_when_not_member(uow, establishment_id):
    actor = make_actor()

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await OperatingHoursReader(uow).list(actor, establishment_id)
