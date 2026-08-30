"""Carregamento das tools do MCP server do AgendaBot via `langchain-mcp-adapters`.

Segunda integração com o mesmo host, em arquivo separado da emissão da sessão
(`session_issuer.py`) porque muda por outro motivo: aqui o contrato é o protocolo
MCP, não a API HTTP.
"""

import asyncio
from collections.abc import Callable, Sequence
from typing import Any, Protocol

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection, StreamableHttpConnection

from src.domain.exceptions import BookingSessionError

_SERVER_NAME = "agendabot"


class _ToolLoader(Protocol):
    """O mínimo que o provider usa de um cliente MCP: carregar as tools."""

    async def get_tools(self) -> list[Any]: ...


ToolLoaderFactory = Callable[[dict[str, Connection]], _ToolLoader]


class AgendaBotToolProvider:
    """Abre uma conexão MCP autenticada por sessão e devolve as tools do AgendaBot.

    Implementa `BookingToolProviderProtocol`. Uma conexão nova a cada chamada: o
    token é a identidade do cliente, e reaproveitar a conexão entre contatos
    agendaria para o cliente errado. O *schema* das tools é cacheável, o cliente
    não — otimização deixada para quando (e se) o custo for medido.

    Qualquer falha ao abrir a conexão ou listar as tools — token recusado com
    `401`, servidor fora do ar, tempo esgotado — vira `BookingSessionError`: o
    caminho principal a trata como as demais falhas de sessão, com uma resposta
    em linguagem natural para o cliente.
    """

    def __init__(
        self,
        *,
        mcp_url: str,
        timeout_seconds: float,
        loader_factory: ToolLoaderFactory = MultiServerMCPClient,
    ) -> None:
        self._mcp_url = mcp_url
        self._timeout_seconds = timeout_seconds
        self._loader_factory = loader_factory

    async def tools_for(self, session_token: str) -> Sequence[Any]:
        """Abre uma conexão MCP autenticada e devolve as tools carregadas."""
        connection: StreamableHttpConnection = {
            "transport": "streamable_http",
            "url": self._mcp_url,
            "headers": {"Authorization": f"Bearer {session_token}"},
        }
        connections: dict[str, Connection] = {_SERVER_NAME: connection}
        loader = self._loader_factory(connections)

        try:
            async with asyncio.timeout(self._timeout_seconds):
                return await loader.get_tools()
        except TimeoutError as exc:
            raise BookingSessionError("Tempo esgotado ao carregar as tools do AgendaBot.") from exc
        except Exception as exc:
            # A pilha do `langchain-mcp-adapters` (task group do anyio + httpx +
            # protocolo MCP) não tem hierarquia de exceção pública estável — um
            # `401` chega embrulhado num `ExceptionGroup`. Como o contrato da
            # porta exige um erro de domínio aqui de qualquer forma, traduzimos
            # tudo. `CancelledError`/`KeyboardInterrupt` são `BaseException` e
            # continuam subindo.
            raise BookingSessionError("Não foi possível carregar as tools do AgendaBot.") from exc
