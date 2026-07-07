import pytest

from app.core.exceptions import ForbiddenError
from app.modules.operating_hours.application.read import OperatingHoursReader
from app.modules.operating_hours.domain.schemas import OperatingHourRead
from tests.modules.operating_hours.application.conftest import make_actor


@pytest.fixture
def reader(mock_uow) -> OperatingHoursReader:
    return OperatingHoursReader(uow=mock_uow)


async def test_list_returns_operating_hour_read(reader, admin_user, establishment_id):
    result = await reader.list(admin_user, establishment_id)

    assert isinstance(result, list)
    assert all(isinstance(h, OperatingHourRead) for h in result)


async def test_list_calls_repo_with_establishment_id(reader, mock_repo, admin_user, establishment_id):
    await reader.list(admin_user, establishment_id)

    mock_repo.list_by_establishment.assert_awaited_once_with(establishment_id)


async def test_list_accessible_by_member(reader, member_user, establishment_id):
    result = await reader.list(member_user, establishment_id)

    assert isinstance(result, list)


async def test_list_forbidden_for_global_admin(reader, global_admin_user, establishment_id):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await reader.list(global_admin_user, establishment_id)


async def test_list_forbidden_when_not_member(reader, establishment_id):
    actor = make_actor()

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await reader.list(actor, establishment_id)
