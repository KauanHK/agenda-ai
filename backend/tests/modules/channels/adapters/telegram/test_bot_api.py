"""Testes de `TelegramBotApi` contra um dublê HTTP (respx)."""

import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from app.modules.channels.adapters.telegram.bot_api import (
    TelegramBotApi,
    build_bot_api_client,
)
from app.modules.channels.domain.entities import BotIdentity
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)

_BOT_TOKEN = "123456:segredo-do-bot"
_SECRET = "s3gr3d0-do-webhook"
_BASE = f"https://api.telegram.org/bot{_BOT_TOKEN}"
_GET_ME = f"{_BASE}/getMe"
_SET = f"{_BASE}/setWebhook"
_DELETE = f"{_BASE}/deleteWebhook"
_INFO = f"{_BASE}/getWebhookInfo"
_WEBHOOK_URL = f"https://agente.exemplo/webhook/telegram/{_SECRET}"


def _info(url: str) -> dict[str, object]:
    return {"ok": True, "result": {"url": url, "pending_update_count": 0}}


@pytest.fixture
async def bot_api() -> AsyncIterator[TelegramBotApi]:
    async with build_bot_api_client() as client:
        yield TelegramBotApi(client)


async def test_get_me_devolve_a_identidade_do_bot(bot_api: TelegramBotApi) -> None:
    with respx.mock:
        respx.post(_GET_ME).mock(
            return_value=httpx.Response(
                200,
                json={"ok": True, "result": {"id": 123456, "username": "agenda_bot"}},
            )
        )
        identity = await bot_api.get_me(_BOT_TOKEN)

    assert identity == BotIdentity(id=123456, username="agenda_bot")


@pytest.mark.parametrize("status", [401, 404])
async def test_token_recusado_levanta_invalid_bot_token_error(
    bot_api: TelegramBotApi, status: int
) -> None:
    with respx.mock:
        respx.post(_GET_ME).mock(
            return_value=httpx.Response(
                status, json={"ok": False, "description": f"Unauthorized {_BOT_TOKEN}"}
            )
        )
        with pytest.raises(InvalidBotTokenError) as excinfo:
            await bot_api.get_me(_BOT_TOKEN)

    assert _BOT_TOKEN not in str(excinfo.value)
    assert excinfo.value.__cause__ is None


async def test_set_webhook_manda_url_segredo_e_updates(bot_api: TelegramBotApi) -> None:
    with respx.mock:
        route = respx.post(_SET).mock(
            return_value=httpx.Response(200, json={"ok": True, "result": True})
        )
        await bot_api.set_webhook(
            _BOT_TOKEN,
            url=_WEBHOOK_URL,
            secret_token=_SECRET,
            drop_pending_updates=True,
        )

    assert json.loads(route.calls.last.request.content) == {
        "url": _WEBHOOK_URL,
        "secret_token": _SECRET,
        "allowed_updates": ["message"],
        "drop_pending_updates": True,
    }


@pytest.mark.parametrize("drop", [True, False])
async def test_delete_webhook_repassa_drop_pending_updates(
    bot_api: TelegramBotApi, drop: bool
) -> None:
    with respx.mock:
        route = respx.post(_DELETE).mock(
            return_value=httpx.Response(200, json={"ok": True, "result": True})
        )
        await bot_api.delete_webhook(_BOT_TOKEN, drop_pending_updates=drop)

    assert json.loads(route.calls.last.request.content) == {
        "drop_pending_updates": drop
    }


async def test_get_webhook_info_mascara_o_segredo_na_url(
    bot_api: TelegramBotApi,
) -> None:
    with respx.mock:
        respx.post(_INFO).mock(
            return_value=httpx.Response(200, json=_info(_WEBHOOK_URL))
        )
        info = await bot_api.get_webhook_info(_BOT_TOKEN)

    assert info == {
        "url": "https://agente.exemplo/webhook/telegram/***",
        "pending_update_count": 0,
    }
    assert _SECRET not in json.dumps(info)


async def test_get_webhook_info_sem_webhook_devolve_url_vazia(
    bot_api: TelegramBotApi,
) -> None:
    with respx.mock:
        respx.post(_INFO).mock(return_value=httpx.Response(200, json=_info("")))
        info = await bot_api.get_webhook_info(_BOT_TOKEN)

    assert info["url"] == ""


_FAILURES = [
    pytest.param(
        httpx.Response(500, json={"ok": False, "description": "Internal Server Error"}),
        id="5xx",
    ),
    pytest.param(
        httpx.Response(
            429,
            json={
                "ok": False,
                "description": "Too Many Requests",
                "parameters": {"retry_after": 3},
            },
        ),
        id="429",
    ),
    pytest.param(httpx.Response(200, json={"ok": False}), id="ok-false"),
    pytest.param(httpx.Response(502, text="bad gateway"), id="sem-json"),
    pytest.param(
        httpx.Response(
            400,
            json={
                "ok": False,
                "description": f"Bad Request: {_BOT_TOKEN} {_SECRET} HTTPS url",
            },
        ),
        id="descricao-com-segredos",
    ),
    pytest.param(httpx.ConnectError("boom"), id="transporte"),
    pytest.param(httpx.ReadTimeout("devagar"), id="timeout"),
]


@pytest.mark.parametrize("outcome", _FAILURES)
async def test_falhas_levantam_telegram_api_error_sem_vazar_segredos(
    bot_api: TelegramBotApi, outcome: httpx.Response | Exception
) -> None:
    with respx.mock:
        route = respx.post(_SET)
        if isinstance(outcome, Exception):
            route.mock(side_effect=outcome)
        else:
            route.mock(return_value=outcome)
        with pytest.raises(TelegramApiError) as excinfo:
            await bot_api.set_webhook(
                _BOT_TOKEN, url=_WEBHOOK_URL, secret_token=_SECRET
            )

    assert _BOT_TOKEN not in str(excinfo.value)
    assert _SECRET not in str(excinfo.value)
    assert excinfo.value.__cause__ is None


async def test_descricao_do_telegram_volta_no_erro_com_os_segredos_mascarados(
    bot_api: TelegramBotApi,
) -> None:
    with respx.mock:
        respx.post(_SET).mock(
            return_value=httpx.Response(
                400,
                json={
                    "ok": False,
                    "description": f"Bad Request: bad webhook {_SECRET}",
                },
            )
        )
        with pytest.raises(TelegramApiError, match=r"bad webhook \*\*\*"):
            await bot_api.set_webhook(
                _BOT_TOKEN, url=_WEBHOOK_URL, secret_token=_SECRET
            )
