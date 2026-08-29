import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination.params import Page, PageParams
from app.modules.unavailabilities.application.dtos.filters import (
    UnavailabilityFilters,
)
from app.modules.unavailabilities.application.use_cases.read import (
    UnavailabilitiesReader,
)
from tests.modules.unavailabilities.application.use_cases.conftest import (
    make_actor,
    make_unavailability,
)


async def test_get_by_id_returns_entity(
    uow, unavailabilities_repo, admin_user, establishment_id
):
    unavailability = make_unavailability(establishment_id)
    unavailabilities_repo.get_by_id.return_value = unavailability

    result = await UnavailabilitiesReader(uow).get_by_id(
        unavailability.id, admin_user, establishment_id
    )

    assert result is unavailability


async def test_get_by_id_raises_not_found_out_of_scope(
    uow, unavailabilities_repo, admin_user, establishment_id
):
    unavailabilities_repo.get_by_id.return_value = make_unavailability(uuid.uuid7())

    with pytest.raises(NotFoundError):
        await UnavailabilitiesReader(uow).get_by_id(
            uuid.uuid7(), admin_user, establishment_id
        )


async def test_get_by_id_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await UnavailabilitiesReader(uow).get_by_id(
            uuid.uuid7(), global_admin_user, establishment_id
        )


async def test_paginate_scopes_to_establishment(
    uow, unavailabilities_repo, member_user, establishment_id
):
    unavailability = make_unavailability(establishment_id)
    unavailabilities_repo.paginate.return_value = Page(
        items=[unavailability], total=1, page=1, page_size=10
    )

    page = await UnavailabilitiesReader(uow).paginate(
        page_params=PageParams(page=1, page_size=10),
        actor=member_user,
        establishment_id=establishment_id,
    )

    assert page.total == 1
    assert page.items == [unavailability]
    unavailabilities_repo.paginate.assert_awaited_once()
    _, kwargs = unavailabilities_repo.paginate.call_args
    sent_filters: UnavailabilityFilters = kwargs["filters"]
    assert sent_filters.establishment_id == establishment_id


async def test_paginate_forbidden_when_not_member(uow, establishment_id):
    actor = make_actor()

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await UnavailabilitiesReader(uow).paginate(
            page_params=PageParams(), actor=actor, establishment_id=establishment_id
        )
