from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastmcp import FastMCP

from app.db.session import db
from app.modules.services.mcp import tools as services_tools


@dataclass
class AppContext: ...


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:

    db.init()
    try:
        yield AppContext()
    finally:
        await db.close()


def create_app() -> FastMCP:

    mcp = FastMCP("agendabot", lifespan=lifespan)
    # mcp.add_middleware(AuthMiddleware())
    services_tools.register_tools(mcp)

    return mcp
