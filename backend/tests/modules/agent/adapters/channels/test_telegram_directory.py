"""Testes do diretório de canais lido do banco."""

import uuid
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.exc import OperationalError

from app.modules.agent.adapters.channels.telegram_directory import (
    DbTelegramChannelDirectory,
)
from app.modules.agent.domain.entities import Establishment, TelegramChannel
from app.modules.agent.domain.exceptions import ChannelLookupError
from tests.modules.channels.fakes import (
    TOKEN,
    FakeChannelsUnitOfWork,
    make_telegram_bot,
)
from tests.modules.establishments.application.use_cases.conftest import (
    make_establishment,
)

_ESTABLISHMENT_ID = uuid.UUID("01a04f64-0000-7000-8000-00000000e001")


def _uow(*, bot: bool = True, active: bool = True, exists: bool = True):
    uow = FakeChannelsUnitOfWork()
    if bot:
        uow.telegram_bots.get_by_establishment.return_value = make_telegram_bot(
            _ESTABLISHMENT_ID
        )
    uow.establishments.get_by_id_or_none.return_value = (
        make_establishment(
            id=_ESTABLISHMENT_ID, timezone="America/Manaus", is_active=active
        )
        if exists
        else None
    )
    return uow


async def _get(uow: FakeChannelsUnitOfWork) -> TelegramChannel | None:
    return await DbTelegramChannelDirectory(lambda: uow).get(_ESTABLISHMENT_ID)


async def test_bot_conectado_e_estabelecimento_ativo_devolve_o_canal() -> None:
    channel = await _get(_uow())

    assert channel == TelegramChannel(
        establishment=Establishment(
            id=_ESTABLISHMENT_ID, timezone=ZoneInfo("America/Manaus")
        ),
        bot_token=TOKEN,
        webhook_secret="segredo-antigo",
    )


async def test_sem_bot_devolve_none() -> None:
    uow = _uow(bot=False)

    assert await _get(uow) is None
    uow.establishments.get_by_id_or_none.assert_not_awaited()


async def test_estabelecimento_inativo_devolve_none() -> None:
    assert await _get(_uow(active=False)) is None


async def test_estabelecimento_excluido_devolve_none() -> None:
    # O repositório ignora os excluídos (`deleted_at`) e devolve `None`.
    assert await _get(_uow(exists=False)) is None


@pytest.mark.parametrize(
    "error", [OperationalError("SELECT", {}, Exception("banco fora")), OSError()]
)
async def test_falha_do_banco_vira_channel_lookup_error(error: Exception) -> None:
    uow = _uow()
    uow.telegram_bots.get_by_establishment.side_effect = error

    with pytest.raises(ChannelLookupError):
        await _get(uow)


def test_repr_nao_expoe_os_segredos() -> None:
    channel = TelegramChannel(
        establishment=Establishment(id=_ESTABLISHMENT_ID, timezone=ZoneInfo("UTC")),
        bot_token=TOKEN,
        webhook_secret="segredo-do-webhook",
    )

    assert TOKEN not in repr(channel)
    assert "segredo-do-webhook" not in repr(channel)
