"""Porta de carregamento das tools do MCP server do AgendaBot."""

from collections.abc import Sequence
from typing import Any, Protocol


class BookingToolProviderProtocol(Protocol):
    """Abre uma conexão MCP autenticada por sessão e devolve as tools do AgendaBot."""

    async def tools_for(self, session_token: str) -> Sequence[Any]:
        """Carrega as tools do MCP server autenticadas com o token da sessão.

        O tipo do elemento é opaco para a aplicação de propósito: quem sabe o que
        é uma tool é o runner do agente, que a recebe e repassa. A aplicação
        apenas garante que o token certo chegou ao provider certo.

        Raises:
            BookingSessionError: Se a conexão MCP falhar — token recusado com
                `401`, servidor fora do ar, ou tempo esgotado no carregamento.
        """
        ...
