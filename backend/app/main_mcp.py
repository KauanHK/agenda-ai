"""
Entrypoint do servidor MCP.

    uv run uvicorn app.main_mcp:app --host 0.0.0.0 --port 8001

Serve o transporte HTTP em `/mcp`, em modo stateless — cada tool call é independente,
o que dispensa sessão fixa e permite escalar em mais de uma réplica.
"""

from starlette.middleware.cors import CORSMiddleware

from app.mcp.server import create_app

mcp = create_app()
app = mcp.http_app(path="/mcp", stateless_http=True)

# Libera o MCP Inspector local (`npx @modelcontextprotocol/inspector`), usado para
# testar as tools na mão durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:6274"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)
