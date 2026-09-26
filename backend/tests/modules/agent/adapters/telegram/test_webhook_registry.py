"""Testes de `TelegramWebhookRegistry` contra um dublê HTTP (respx)."""

import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from app.modules.agent.adapters.telegram.client import build_telegram_client
from app.modules.agent.adapters.telegram.webhook_registry import TelegramWebhookRegistry
from app.modules.agent.domain.exceptions import WebhookRegistrationError

_BOT_TOKEN = "123456:segredo-do-bot"
_SECRET = "s3gr3d0-do-webhook"
_BASE = f"https://api.telegram.org/bot{_BOT_TOKEN}"
_SET = f"{_BASE}/setWebhook"
_INFO = f"{_BASE}/getWebhookInfo"


def _info(url: str) -> dict[str, object]:
    return {"ok": True, "result": {"url": url, "pending_update_count": 0}}


@pytest.fixture
async def registry() -> AsyncIterator[TelegramWebhookRegistry]:
    client = build_telegram_client(
        api_root="https://api.telegram.org",
        bot_token=_BOT_TOKEN,
        connect_timeout_seconds=5.0,
        read_timeout_seconds=5.0,
    )
    async with client:
        yield TelegramWebhookRegistry(client, webhook_secret=_SECRET)


def test_webhook_url_monta_caminho_com_o_segredo_sem_barra_dupla(
    registry: TelegramWebhookRegistry,
) -> None:
    assert registry.webhook_url("https://agente.exemplo/") == (
        f"https://agente.exemplo/webhook/telegram/{_SECRET}"
    )


async def test_register_faz_setwebhook_e_devolve_info_mascarada(
    registry: TelegramWebhookRegistry,
) -> None:
    with respx.mock:
        set_route = respx.post(_SET).mock(
            return_value=httpx.Response(200, json={"ok": True, "result": True})
        )
        respx.post(_INFO).mock(
            return_value=httpx.Response(
                200, json=_info(f"https://agente.exemplo/webhook/telegram/{_SECRET}")
            )
        )
        info = await registry.register("https://agente.exemplo", drop_pending_updates=True)

    assert json.loads(set_route.calls.last.request.content) == {
        "url": f"https://agente.exemplo/webhook/telegram/{_SECRET}",
        "secret_token": _SECRET,
        "allowed_updates": ["message"],
        "drop_pending_updates": True,
    }
    assert info == {"url": "https://agente.exemplo/webhook/telegram/***", "pending_update_count": 0}


async def test_info_mascara_o_segredo_na_url(registry: TelegramWebhookRegistry) -> None:
    with respx.mock:
        respx.post(_INFO).mock(
            return_value=httpx.Response(200, json=_info(f"https://x/webhook/telegram/{_SECRET}"))
        )
        info = await registry.info()

    assert info["url"] == "https://x/webhook/telegram/***"
    assert _SECRET not in json.dumps(info)


async def test_info_sem_webhook_registrado_devolve_url_vazia(
    registry: TelegramWebhookRegistry,
) -> None:
    with respx.mock:
        respx.post(_INFO).mock(return_value=httpx.Response(200, json=_info("")))
        info = await registry.info()

    assert info["url"] == ""


async def test_recusa_do_telegram_vira_webhook_registration_error_com_descricao(
    registry: TelegramWebhookRegistry,
) -> None:
    with respx.mock:
        respx.post(_SET).mock(
            return_value=httpx.Response(
                400, json={"ok": False, "description": "Bad Request: bad webhook: HTTPS url"}
            )
        )
        with pytest.raises(WebhookRegistrationError, match="HTTPS url"):
            await registry.register("https://agente.exemplo")


async def test_ok_false_com_http_200_tambem_falha(registry: TelegramWebhookRegistry) -> None:
    with respx.mock:
        respx.post(_INFO).mock(return_value=httpx.Response(200, json={"ok": False}))
        with pytest.raises(WebhookRegistrationError, match="HTTP 200"):
            await registry.info()


async def test_resposta_sem_json_falha(registry: TelegramWebhookRegistry) -> None:
    with respx.mock:
        respx.post(_INFO).mock(return_value=httpx.Response(502, text="bad gateway"))
        with pytest.raises(WebhookRegistrationError, match="sem JSON"):
            await registry.info()


async def test_falha_de_transporte_nao_vaza_o_token(registry: TelegramWebhookRegistry) -> None:
    with respx.mock:
        respx.post(_SET).mock(side_effect=httpx.ConnectError("boom"))
        with pytest.raises(WebhookRegistrationError) as excinfo:
            await registry.register("https://agente.exemplo")

    assert _BOT_TOKEN not in str(excinfo.value)
    assert excinfo.value.__cause__ is None
