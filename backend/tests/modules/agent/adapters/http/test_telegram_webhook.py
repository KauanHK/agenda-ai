"""Testes do webhook do Telegram com um container fake.

O container real toca banco, Redis e LLM no boot; aqui a rota é montada sozinha
sobre um fake que só registra os updates recebidos, com um diretório em memória.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.modules.agent.adapters.http.routes import telegram
from app.modules.agent.domain.entities import Establishment, TelegramChannel
from tests.modules.agent.fakes.channel_directory import FakeChannelDirectory

_HEADER = "X-Telegram-Bot-Api-Secret-Token"
_CHANNEL_A = TelegramChannel(
    establishment=Establishment(
        id=uuid.UUID("01a04f64-0000-7000-8000-00000000e001"),
        timezone=ZoneInfo("America/Sao_Paulo"),
    ),
    bot_token="111:token-a",
    webhook_secret="segredo-a",
)
_CHANNEL_B = TelegramChannel(
    establishment=Establishment(
        id=uuid.UUID("01a04f64-0000-7000-8000-00000000e002"),
        timezone=ZoneInfo("America/Manaus"),
    ),
    bot_token="222:token-b",
    webhook_secret="segredo-b",
)
_URL_A = f"/webhook/telegram/{_CHANNEL_A.establishment.id}"
_UPDATE = {"update_id": 10, "message": {"text": "oi"}}


class _FakeContainer:
    """Só o que a rota usa: o diretório e a coroutine de processamento."""

    def __init__(
        self,
        *,
        channels: FakeChannelDirectory | None = None,
        handle_update: Callable[[Mapping[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        self.channels = channels or FakeChannelDirectory(_CHANNEL_A, _CHANNEL_B)
        self.received: list[tuple[Establishment, Mapping[str, Any]]] = []
        self._handle_update = handle_update

    async def handle_update(
        self, establishment: Establishment, payload: Mapping[str, Any]
    ) -> None:
        self.received.append((establishment, payload))
        if self._handle_update is not None:
            await self._handle_update(payload)


def _app(container: _FakeContainer) -> FastAPI:
    app = FastAPI()
    app.include_router(telegram.router)
    app.state.container = container
    app.state.background_tasks = set()
    return app


@pytest.fixture
def container() -> _FakeContainer:
    return _FakeContainer()


@pytest.fixture
async def client(container: _FakeContainer) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        yield client


async def test_segredo_certo_responde_200_e_processa_no_estabelecimento_do_bot(
    client: AsyncClient, container: _FakeContainer
) -> None:
    response = await client.post(_URL_A, json=_UPDATE, headers={_HEADER: "segredo-a"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    await asyncio.sleep(0.05)
    assert container.received == [(_CHANNEL_A.establishment, _UPDATE)]


@pytest.mark.parametrize(
    ("url", "headers"),
    [
        pytest.param(
            "/webhook/telegram/nao-e-uuid", {_HEADER: "segredo-a"}, id="id-invalido"
        ),
        pytest.param(
            f"/webhook/telegram/{uuid.uuid4()}", {_HEADER: "segredo-a"}, id="sem-bot"
        ),
        pytest.param(_URL_A, {}, id="sem-header"),
        pytest.param(_URL_A, {_HEADER: "impostor"}, id="header-errado"),
        pytest.param(_URL_A, {_HEADER: "segredo-b"}, id="segredo-de-outro-bot"),
        pytest.param(
            _URL_A, {_HEADER: "segrédo".encode("latin-1")}, id="header-nao-ascii"
        ),
    ],
)
async def test_rejeicoes_respondem_404_e_nao_processam(
    client: AsyncClient,
    container: _FakeContainer,
    url: str,
    headers: dict[str, str | bytes],
) -> None:
    response = await client.post(url, json=_UPDATE, headers=headers)

    assert response.status_code == 404
    await asyncio.sleep(0.05)
    assert container.received == []


async def test_diretorio_fora_responde_503_e_nao_processa() -> None:
    container = _FakeContainer(channels=FakeChannelDirectory(_CHANNEL_A, fail=True))
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        response = await client.post(
            _URL_A, json=_UPDATE, headers={_HEADER: "segredo-a"}
        )

    assert response.status_code == 503
    await asyncio.sleep(0.05)
    assert container.received == []


async def test_responde_200_antes_de_o_processamento_terminar() -> None:
    gate = asyncio.Event()

    async def blocks(_payload: Mapping[str, Any]) -> None:
        await gate.wait()

    container = _FakeContainer(handle_update=blocks)
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        response = await client.post(
            _URL_A, json={"update_id": 7}, headers={_HEADER: "segredo-a"}
        )
        assert response.status_code == 200

        await asyncio.sleep(0.05)
        # Começou e ainda está preso no gate.
        assert container.received == [(_CHANNEL_A.establishment, {"update_id": 7})]
        gate.set()


async def test_falha_no_processamento_em_background_nao_afeta_a_resposta() -> None:
    async def boom(_payload: Mapping[str, Any]) -> None:
        raise RuntimeError("processamento explodiu")

    container = _FakeContainer(handle_update=boom)
    async with AsyncClient(
        transport=ASGITransport(app=_app(container)), base_url="http://test"
    ) as client:
        response = await client.post(
            _URL_A, json={"update_id": 9}, headers={_HEADER: "segredo-a"}
        )

    assert response.status_code == 200
    await asyncio.sleep(0.05)
