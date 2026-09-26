"""
Autenticação do servidor MCP.

O agente de IA apresenta o token de sessão do cliente como bearer token. Verificar isso
num `TokenVerifier` — e não num middleware de tool — faz o FastMCP recusar a conexão
com 401 antes de qualquer tool rodar, e disponibiliza os claims verificados via
`CurrentAccessToken`.
"""

from fastmcp.server.auth import AccessToken, TokenVerifier

from app.core.exceptions import UnauthorizedError
from app.core.security.mcp_tokens import decode_client_mcp_session_token

# Identifica a origem do token nos logs do FastMCP; não é um id de cliente OAuth nosso.
_TOKEN_CLIENT_ID = "agendabot-customer-session"


class SessionTokenVerifier(TokenVerifier):
    """Verifica o token de sessão que o agente emite para o cliente."""

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Valida o token e expõe o contexto do cliente como claims.

        Args:
            token (str): O bearer token recebido.

        Returns:
            AccessToken | None:
                O token com os claims da sessão, ou `None` se for inválido ou
                expirado — o FastMCP traduz `None` em 401.
        """

        try:
            payload = decode_client_mcp_session_token(token)
        except UnauthorizedError:
            return None

        return AccessToken(
            token=token,
            client_id=_TOKEN_CLIENT_ID,
            scopes=[],
            subject=str(payload["client_id"]),
            claims={
                "client_id": str(payload["client_id"]),
                "establishment_id": str(payload["establishment_id"]),
                "phone": payload["phone"],
            },
        )
