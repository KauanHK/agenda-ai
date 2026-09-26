"""Testes de `TelegramMessenger` contra um dublê HTTP (respx)."""

import json
import uuid
from collections.abc import AsyncIterator
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx

from app.modules.agent.adapters.telegram.client import (
    TelegramMessenger,
    build_telegram_client,
)
from app.modules.agent.adapters.telegram.formatting import TELEGRAM_MAX_CHARS
from app.modules.agent.domain.entities import (
    Channel,
    ConversationRef,
    Establishment,
    TelegramChannel,
)
from app.modules.agent.domain.exceptions import DeliveryError
from tests.modules.agent.fakes.channel_directory import FakeChannelDirectory

_BOT_TOKEN = "123456:segredo-do-bot"
_BASE = f"https://api.telegram.org/bot{_BOT_TOKEN}"
_SEND = f"{_BASE}/sendMessage"
_ACTION = f"{_BASE}/sendChatAction"

_OTHER_TOKEN = "654321:outro-bot"
_OTHER_SEND = f"https://api.telegram.org/bot{_OTHER_TOKEN}/sendMessage"


def _channel(establishment_id: str, bot_token: str) -> TelegramChannel:
    return TelegramChannel(
        establishment=Establishment(
            id=uuid.UUID(establishment_id), timezone=ZoneInfo("America/Sao_Paulo")
        ),
        bot_token=bot_token,
        webhook_secret="segredo",
    )


_CHANNEL = _channel("01a04f64-0000-7000-8000-00000000e001", _BOT_TOKEN)
_OTHER_CHANNEL = _channel("01a04f64-0000-7000-8000-00000000e002", _OTHER_TOKEN)

_REF = ConversationRef(
    channel=Channel.TELEGRAM,
    establishment_id=_CHANNEL.establishment.id,
    channel_user_id="42",
)
_OTHER_REF = ConversationRef(
    channel=Channel.TELEGRAM,
    establishment_id=_OTHER_CHANNEL.establishment.id,
    channel_user_id="42",
)


@pytest.fixture
def directory() -> FakeChannelDirectory:
    return FakeChannelDirectory(_CHANNEL, _OTHER_CHANNEL)


@pytest.fixture
async def messenger(
    directory: FakeChannelDirectory,
) -> AsyncIterator[TelegramMessenger]:
    client = build_telegram_client(
        api_root="https://api.telegram.org",
        connect_timeout_seconds=5.0,
        read_timeout_seconds=5.0,
    )
    async with client:
        yield TelegramMessenger(client, directory, connect_retry_delay_seconds=0.0)


async def test_send_text_faz_sendmessage_com_chat_id_e_texto(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(return_value=httpx.Response(200, json={"ok": True}))
        await messenger.send_text(_REF, "Beleza, **marcado**!")

    assert route.call_count == 1
    assert json.loads(route.calls.last.request.content) == {
        "chat_id": "42",
        "text": "Beleza, marcado!",
    }


async def test_send_text_quebra_texto_longo_em_varios_envios(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(return_value=httpx.Response(200, json={"ok": True}))
        await messenger.send_text(_REF, "palavra " * 900)

    assert route.call_count > 1
    for call in route.calls:
        body = json.loads(call.request.content)
        assert len(body["text"]) <= TELEGRAM_MAX_CHARS


async def test_texto_vazio_apos_normalizar_nao_envia_nada(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(return_value=httpx.Response(200, json={"ok": True}))
        await messenger.send_text(_REF, "##")

    assert route.call_count == 0


async def test_429_respeita_retry_after_e_tenta_uma_vez(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(
            side_effect=[
                httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 0}}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        await messenger.send_text(_REF, "oi")

    assert route.call_count == 2


async def test_429_persistente_vira_delivery_error(messenger: TelegramMessenger) -> None:
    with respx.mock:
        respx.post(_SEND).mock(
            return_value=httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 0}})
        )
        with pytest.raises(DeliveryError):
            await messenger.send_text(_REF, "oi")


async def test_erro_http_vira_delivery_error(messenger: TelegramMessenger) -> None:
    with respx.mock:
        respx.post(_SEND).mock(return_value=httpx.Response(400, json={"ok": False}))
        with pytest.raises(DeliveryError):
            await messenger.send_text(_REF, "oi")


async def test_falha_de_transporte_vira_delivery_error_sem_vazar_o_token(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(side_effect=httpx.ConnectError("recusado"))
        with pytest.raises(DeliveryError) as exc_info:
            await messenger.send_text(_REF, "oi")

    assert route.call_count == 2  # tentou de novo por ser falha de conexão
    assert _BOT_TOKEN not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


async def test_erro_de_conexao_repete_uma_vez_e_entao_envia(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(
            side_effect=[httpx.ConnectError("recusado"), httpx.Response(200, json={"ok": True})]
        )
        await messenger.send_text(_REF, "oi")

    assert route.call_count == 2


@pytest.mark.parametrize(
    "timeout",
    [httpx.ReadTimeout("lento"), httpx.WriteTimeout("lento"), httpx.PoolTimeout("sem conexão")],
)
async def test_timeout_depois_do_request_sair_nao_repete(
    messenger: TelegramMessenger, timeout: httpx.TimeoutException
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(side_effect=timeout)
        with pytest.raises(DeliveryError):
            await messenger.send_text(_REF, "oi")

    assert route.call_count == 1  # não repete: sendMessage pode ter saído


async def test_signal_typing_engole_falha(messenger: TelegramMessenger) -> None:
    with respx.mock:
        respx.post(_ACTION).mock(side_effect=httpx.ConnectError("caiu"))
        await messenger.signal_typing(_REF)  # não levanta


async def test_signal_typing_manda_action_typing(messenger: TelegramMessenger) -> None:
    with respx.mock:
        route = respx.post(_ACTION).mock(return_value=httpx.Response(200, json={"ok": True}))
        await messenger.signal_typing(_REF)

    assert json.loads(route.calls.last.request.content) == {"chat_id": "42", "action": "typing"}


async def test_cada_conversa_sai_pelo_bot_do_seu_estabelecimento(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route_a = respx.post(_SEND).mock(return_value=httpx.Response(200, json={"ok": True}))
        route_b = respx.post(_OTHER_SEND).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await messenger.send_text(_REF, "para o A")
        await messenger.send_text(_OTHER_REF, "para o B")

    assert [json.loads(c.request.content)["text"] for c in route_a.calls] == ["para o A"]
    assert [json.loads(c.request.content)["text"] for c in route_b.calls] == ["para o B"]


async def test_bot_desconectado_no_meio_do_turno_vira_delivery_error(
    messenger: TelegramMessenger, directory: FakeChannelDirectory
) -> None:
    del directory.channels[_CHANNEL.establishment.id]

    # Sem rota no respx: qualquer chamada ao Telegram falharia o teste.
    with respx.mock, pytest.raises(DeliveryError):
        await messenger.send_text(_REF, "oi")


async def test_diretorio_fora_vira_delivery_error(
    messenger: TelegramMessenger, directory: FakeChannelDirectory
) -> None:
    directory.fail = True

    with respx.mock, pytest.raises(DeliveryError) as exc_info:
        await messenger.send_text(_REF, "oi")

    assert exc_info.value.__cause__ is None


async def test_erro_http_nao_carrega_o_token(messenger: TelegramMessenger) -> None:
    with respx.mock:
        respx.post(_SEND).mock(return_value=httpx.Response(400, json={"ok": False}))
        with pytest.raises(DeliveryError) as exc_info:
            await messenger.send_text(_REF, "oi")

    assert _BOT_TOKEN not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


async def test_signal_typing_sem_bot_ou_com_diretorio_fora_nao_levanta(
    messenger: TelegramMessenger, directory: FakeChannelDirectory
) -> None:
    del directory.channels[_CHANNEL.establishment.id]
    with respx.mock:
        await messenger.signal_typing(_REF)

    directory.fail = True
    with respx.mock:
        await messenger.signal_typing(_OTHER_REF)
