import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.unavailabilities.application.use_cases.delete import (
    UnavailabilitiesDeleter,
)
from tests.modules.unavailabilities.application.use_cases.conftest import (
    make_unavailability,
)


async def test_delete_calls_repo_with_id(
    uow, unavailabilities_repo, admin_user, establishment_id
):
    existing = make_unavailability(establishment_id)
    unavailabilities_repo.get_by_id.return_value = existing

    await UnavailabilitiesDeleter(uow).delete(existing.id, admin_user, establishment_id)

    unavailabilities_repo.delete.assert_awaited_once_with(existing.id)


async def test_delete_raises_not_found_out_of_scope(
    uow, unavailabilities_repo, admin_user, establishment_id
):
    unavailabilities_repo.get_by_id.return_value = make_unavailability(uuid.uuid7())

    with pytest.raises(NotFoundError):
        await UnavailabilitiesDeleter(uow).delete(
            uuid.uuid7(), admin_user, establishment_id
        )
    unavailabilities_repo.delete.assert_not_awaited()


async def test_delete_forbidden_for_member(uow, member_user, establishment_id):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await UnavailabilitiesDeleter(uow).delete(
            uuid.uuid7(), member_user, establishment_id
        )
