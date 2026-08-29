"""
Servidor MCP do AgendaBot.

Expõe ao agente de IA tudo o que ele precisa para conversar com um cliente e marcar um
horário. Roda no mesmo código da API (mesma imagem, processo separado), acessando os
use cases diretamente — sem uma volta por HTTP.

Cada conexão é autenticada pelo token de sessão do cliente, emitido pelo backend a
partir do telefone. O agente nunca conhece o telefone nem o `client_id`.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.db.session import db
from app.mcp.auth import SessionTokenVerifier
from app.modules.booking.adapters.mcp import tools as booking_tools

INSTRUCTIONS = """
Servidor de agendamentos do AgendaBot.

O cliente já está identificado pela sessão: nunca peça a ele o telefone, e não existem
parâmetros de cliente ou de estabelecimento nas tools.

Fluxo esperado: `list_services` para descobrir o que é oferecido,
`list_available_slots` para ver os horários livres de um serviço num dia, e só então
`create_scheduling`. Ofereça apenas horários que vieram de `list_available_slots`.

Toda tool responde `{"success": true, "data": ...}` ou
`{"success": false, "error_code": ..., "message": ...}`. Em caso de erro, use a
`message` para explicar a situação ao cliente em linguagem natural.
""".strip()


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Abre e fecha o pool de conexões com o banco junto com o servidor."""

    db.init()
    try:
        yield
    finally:
        await db.close()


def create_app() -> FastMCP:
    """Monta o servidor MCP com autenticação e tools registradas."""

    mcp = FastMCP(
        "agendabot",
        instructions=INSTRUCTIONS,
        auth=SessionTokenVerifier(),
        lifespan=lifespan,
    )

    booking_tools.register_tools(mcp)

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return mcp
