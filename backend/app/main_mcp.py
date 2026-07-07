from starlette.middleware.cors import CORSMiddleware

from app.mcp.server import create_app

mcp = create_app()
app = mcp.http_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:6274"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)
