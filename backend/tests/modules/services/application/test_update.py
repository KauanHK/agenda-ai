import uuid
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.services.application.update import ServicesUpdater
from app.modules.services.domain.schemas import ServiceRead, ServiceUpdate


@pytest.fixture
def updater(mock_uow) -> ServicesUpdater:
    return ServicesUpdater(uow=mock_uow)


async def test_update_returns_service_read(updater, admin_user, establishment_id, service_model):
    data = ServiceUpdate(name="Novo Nome")

    result = await updater.update(service_model.id, data, admin_user, establishment_id)

    assert isinstance(result, ServiceRead)


async def test_update_only_updates_sent_fields(updater, admin_user, establishment_id, service_model):
    original_description = service_model.description
    original_duration = service_model.duration_minutes
    original_price = service_model.price
    original_active = service_model.is_active

    await updater.update(
        service_model.id,
        ServiceUpdate(name="Apenas Nome"),
        admin_user,
        establishment_id,
    )

    assert service_model.name == "Apenas Nome"
    assert service_model.description == original_description
    assert service_model.duration_minutes == original_duration
    assert service_model.price == original_price
    assert service_model.is_active is original_active


async def test_update_calls_get_by_id_and_update(
    updater, mock_repo, admin_user, establishment_id, service_model
):
    await updater.update(service_model.id, ServiceUpdate(name="X"), admin_user, establishment_id)

    mock_repo.get_by_id.assert_awaited_once_with(service_model.id)
    mock_repo.update.assert_awaited_once()


async def test_update_raises_not_found_for_other_tenant(
    updater, admin_user, establishment_id, service_model
):
    service_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await updater.update(
            service_model.id,
            ServiceUpdate(name="X"),
            admin_user,
            establishment_id,
        )


async def test_update_raises_conflict_on_integrity_error(
    updater, mock_repo, admin_user, establishment_id, service_model
):
    mock_repo.update.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="Já existe um serviço"):
        await updater.update(
            service_model.id,
            ServiceUpdate(name="Existente"),
            admin_user,
            establishment_id,
        )


async def test_update_forbidden_for_member(updater, member_user, establishment_id, service_model):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await updater.update(service_model.id, ServiceUpdate(name="X"), member_user, establishment_id)


async def test_update_forbidden_for_global_admin(
    updater, global_admin_user, establishment_id, service_model
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await updater.update(
            service_model.id, ServiceUpdate(name="X"), global_admin_user, establishment_id
        )


async def test_update_can_change_is_active(updater, admin_user, establishment_id, service_model):
    service_model.is_active = True

    await updater.update(
        service_model.id,
        ServiceUpdate(is_active=False),
        admin_user,
        establishment_id,
    )

    assert service_model.is_active is False


async def test_update_can_change_price_and_duration(updater, admin_user, establishment_id, service_model):
    new_price = Decimal("99.99")
    new_duration = 90

    await updater.update(
        service_model.id,
        ServiceUpdate(price=new_price, duration_minutes=new_duration),
        admin_user,
        establishment_id,
    )

    assert service_model.price == new_price
    assert service_model.duration_minutes == new_duration
