"""Testes de `AgendaBotToolProvider` contra um cliente MCP dublê."""

import asyncio
from collections.abc import Sequence
from typing import Any

import pytest

from app.modules.agent.adapters.mcp_client.tool_provider import AgendaBotToolProvider
from app.modules.agent.domain.exceptions import BookingSessionError

_MCP_URL = "https://agenda.test/mcp"
_TOKEN = "jwt-real.do-estabelecimento.assinatura-secreta"


class _StubLoader:
    """Cliente MCP mínimo: devolve tools roteirizadas, levanta, ou demora."""

    def __init__(
        self,
        *,
        tools: Sequence[Any] | None = None,
        error: BaseException | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        self._tools = list(tools or [])
        self._error = error
        self._delay_seconds = delay_seconds

    async def get_tools(self) -> list[Any]:
        if self._delay_seconds:
            await asyncio.sleep(self._delay_seconds)
        if self._error is not None:
            raise self._error
        return list(self._tools)


def _provider(
    loader: _StubLoader, *, timeout_seconds: float = 5.0
) -> tuple[AgendaBotToolProvider, dict[str, Any]]:
    captured: dict[str, Any] = {}

    def factory(connections: dict[str, Any]) -> _StubLoader:
        captured["connections"] = connections
        return loader

    provider = AgendaBotToolProvider(
        mcp_url=_MCP_URL,
        timeout_seconds=timeout_seconds,
        loader_factory=factory,
    )
    return provider, captured


async def test_abre_conexao_streamable_http_autenticada_com_bearer() -> None:
    provider, captured = _provider(_StubLoader(tools=["t"]))

    await provider.tools_for(_TOKEN)

    assert captured["connections"] == {
        "agendabot": {
            "transport": "streamable_http",
            "url": _MCP_URL,
            "headers": {"Authorization": f"Bearer {_TOKEN}"},
        }
    }


async def test_devolve_as_tools_carregadas_pelo_cliente() -> None:
    tools = ["list_services", "create_scheduling"]
    provider, _ = _provider(_StubLoader(tools=tools))

    assert list(await provider.tools_for(_TOKEN)) == tools


async def test_timeout_vira_booking_session_error() -> None:
    provider, _ = _provider(_StubLoader(delay_seconds=1.0), timeout_seconds=0.01)

    with pytest.raises(BookingSessionError, match="Tempo esgotado"):
        await provider.tools_for(_TOKEN)


async def test_falha_de_conexao_embrulhada_em_group_vira_booking_session_error() -> None:
    group = ExceptionGroup("unhandled errors in a TaskGroup", [ConnectionError("recusado")])
    provider, _ = _provider(_StubLoader(error=group))

    with pytest.raises(BookingSessionError):
        await provider.tools_for(_TOKEN)


async def test_erro_generico_do_cliente_vira_booking_session_error() -> None:
    provider, _ = _provider(_StubLoader(error=RuntimeError("protocolo MCP quebrou")))

    with pytest.raises(BookingSessionError):
        await provider.tools_for(_TOKEN)


async def test_o_session_token_nunca_aparece_em_mensagem_de_erro() -> None:
    vazado = RuntimeError(f"debug header -> Authorization: Bearer {_TOKEN}")
    provider, _ = _provider(_StubLoader(error=vazado))

    with pytest.raises(BookingSessionError) as exc_info:
        await provider.tools_for(_TOKEN)

    assert _TOKEN not in str(exc_info.value)
    assert _TOKEN not in repr(exc_info.value)


async def test_cancelamento_nao_e_convertido_em_erro_de_dominio() -> None:
    provider, _ = _provider(_StubLoader(error=asyncio.CancelledError()))

    with pytest.raises(asyncio.CancelledError):
        await provider.tools_for(_TOKEN)
