import dataclasses
import uuid
from datetime import datetime

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.types import UNSET
from app.modules.clients.application.use_cases.delete import ClientsDeleter
from app.modules.clients.domain.entities import UpdateClient


async def test_delete_marks_deleted_at(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    await ClientsDeleter(uow).delete(client_entity.id, admin_user, establishment_id)

    clients_repo.update.assert_awaited_once()
    sent: UpdateClient = clients_repo.update.call_args.kwargs["update_command"]
    assert isinstance(sent.deleted_at, datetime)
    assert sent.name is UNSET
    assert sent.is_active is UNSET
    assert clients_repo.update.call_args.kwargs["id_"] == client_entity.id


async def test_delete_raises_not_found_for_other_tenant(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    clients_repo.get_by_id.return_value = dataclasses.replace(
        client_entity, establishment_id=uuid.uuid7()
    )

    with pytest.raises(NotFoundError):
        await ClientsDeleter(uow).delete(
            client_entity.id, admin_user, establishment_id
        )


async def test_delete_forbidden_for_member(
    uow, member_user, establishment_id, client_entity
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await ClientsDeleter(uow).delete(
            client_entity.id, member_user, establishment_id
        )
