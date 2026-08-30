"""Testes do webhook do Telegram com `TestClient` e um container fake.

O container real toca Redis, AgendaBot e LLM no boot; aqui a rota é montada
sozinha sobre um fake que só registra os updates recebidos.
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.interfaces.http.routes import telegram

_SECRET = "s3gr3d0-do-webhook"


class _FakeContainer:
    """Só o que a rota usa: o segredo e a coroutine de processamento."""

    def __init__(
        self,
        *,
        handle_update: Callable[[Mapping[str, Any]], Awaitable[None]] | None = None,
        webhook_secret: str = _SECRET,
    ) -> None:
        self.webhook_secret = webhook_secret
        self.received: list[Mapping[str, Any]] = []
        self._handle_update = handle_update

    async def handle_update(self, payload: Mapping[str, Any]) -> None:
        self.received.append(payload)
        if self._handle_update is not None:
            await self._handle_update(payload)


def _app(container: _FakeContainer) -> FastAPI:
    app = FastAPI()
    app.include_router(telegram.router)
    app.state.container = container
    app.state.background_tasks = set()
    return app


@pytest.fixture
async def context() -> AsyncIterator[tuple[AsyncClient, _FakeContainer]]:
    container = _FakeContainer()
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        yield client, container


async def test_secret_certo_responde_200_e_agenda_o_processamento(
    context: tuple[AsyncClient, _FakeContainer],
) -> None:
    client, container = context
    update = {"update_id": 10, "message": {"text": "oi"}}

    response = await client.post(f"/webhook/telegram/{_SECRET}", json=update)

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    await asyncio.sleep(0.05)
    assert container.received == [update]


async def test_secret_errado_responde_404_e_nao_processa(
    context: tuple[AsyncClient, _FakeContainer],
) -> None:
    client, container = context

    response = await client.post("/webhook/telegram/errado", json={"update_id": 1})

    assert response.status_code == 404
    await asyncio.sleep(0.05)
    assert container.received == []


async def test_header_secret_token_errado_responde_404() -> None:
    container = _FakeContainer()
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/webhook/telegram/{_SECRET}",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "impostor"},
        )

    assert response.status_code == 404


async def test_responde_200_antes_de_o_processamento_terminar() -> None:
    gate = asyncio.Event()

    async def blocks(_payload: Mapping[str, Any]) -> None:
        await gate.wait()

    container = _FakeContainer(handle_update=blocks)
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        response = await client.post(f"/webhook/telegram/{_SECRET}", json={"update_id": 7})
        assert response.status_code == 200

        await asyncio.sleep(0.05)
        assert container.received == [{"update_id": 7}]  # começou, ainda preso no gate
        gate.set()


async def test_falha_no_processamento_em_background_nao_afeta_a_resposta() -> None:
    async def boom(_payload: Mapping[str, Any]) -> None:
        raise RuntimeError("processamento explodiu")

    container = _FakeContainer(handle_update=boom)
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        response = await client.post(f"/webhook/telegram/{_SECRET}", json={"update_id": 9})

    assert response.status_code == 200
    await asyncio.sleep(0.05)
