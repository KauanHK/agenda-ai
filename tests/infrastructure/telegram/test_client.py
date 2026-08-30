"""Testes de `TelegramMessenger` contra um dublê HTTP (respx)."""

import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from src.domain.entities import Channel, Contact
from src.domain.exceptions import DeliveryError
from src.infrastructure.telegram.client import TelegramMessenger, build_telegram_client
from src.infrastructure.telegram.formatting import TELEGRAM_MAX_CHARS

_BOT_TOKEN = "123456:segredo-do-bot"
_BASE = f"https://api.telegram.org/bot{_BOT_TOKEN}"
_SEND = f"{_BASE}/sendMessage"
_ACTION = f"{_BASE}/sendChatAction"

_CONTACT = Contact(
    channel=Channel.TELEGRAM,
    channel_user_id="42",
    display_name="Kauan",
    phone="5547999111222",
)


@pytest.fixture
async def messenger() -> AsyncIterator[TelegramMessenger]:
    client = build_telegram_client(
        api_root="https://api.telegram.org",
        bot_token=_BOT_TOKEN,
        connect_timeout_seconds=5.0,
        read_timeout_seconds=5.0,
    )
    async with client:
        yield TelegramMessenger(client, connect_retry_delay_seconds=0.0)


async def test_send_text_faz_sendmessage_com_chat_id_e_texto(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(return_value=httpx.Response(200, json={"ok": True}))
        await messenger.send_text(_CONTACT, "Beleza, **marcado**!")

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
        await messenger.send_text(_CONTACT, "palavra " * 900)

    assert route.call_count > 1
    for call in route.calls:
        body = json.loads(call.request.content)
        assert len(body["text"]) <= TELEGRAM_MAX_CHARS


async def test_texto_vazio_apos_normalizar_nao_envia_nada(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(return_value=httpx.Response(200, json={"ok": True}))
        await messenger.send_text(_CONTACT, "##")

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
        await messenger.send_text(_CONTACT, "oi")

    assert route.call_count == 2


async def test_429_persistente_vira_delivery_error(messenger: TelegramMessenger) -> None:
    with respx.mock:
        respx.post(_SEND).mock(
            return_value=httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 0}})
        )
        with pytest.raises(DeliveryError):
            await messenger.send_text(_CONTACT, "oi")


async def test_erro_http_vira_delivery_error(messenger: TelegramMessenger) -> None:
    with respx.mock:
        respx.post(_SEND).mock(return_value=httpx.Response(400, json={"ok": False}))
        with pytest.raises(DeliveryError):
            await messenger.send_text(_CONTACT, "oi")


async def test_falha_de_transporte_vira_delivery_error_sem_vazar_o_token(
    messenger: TelegramMessenger,
) -> None:
    with respx.mock:
        route = respx.post(_SEND).mock(side_effect=httpx.ConnectError("recusado"))
        with pytest.raises(DeliveryError) as exc_info:
            await messenger.send_text(_CONTACT, "oi")

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
        await messenger.send_text(_CONTACT, "oi")

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
            await messenger.send_text(_CONTACT, "oi")

    assert route.call_count == 1  # não repete: sendMessage pode ter saído


async def test_signal_typing_engole_falha(messenger: TelegramMessenger) -> None:
    with respx.mock:
        respx.post(_ACTION).mock(side_effect=httpx.ConnectError("caiu"))
        await messenger.signal_typing(_CONTACT)  # não levanta


async def test_signal_typing_manda_action_typing(messenger: TelegramMessenger) -> None:
    with respx.mock:
        route = respx.post(_ACTION).mock(return_value=httpx.Response(200, json={"ok": True}))
        await messenger.signal_typing(_CONTACT)

    assert json.loads(route.calls.last.request.content) == {"chat_id": "42", "action": "typing"}
