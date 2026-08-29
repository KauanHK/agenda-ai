import uuid

from app.core.security.access_tokens import TokenIdentity, create_access_token
from app.core.security.mcp_tokens import create_client_mcp_session_token
from app.mcp.auth import SessionTokenVerifier


class TestSessionTokenVerifier:
    async def test_aceita_token_de_sessao_e_expoe_a_identidade(self) -> None:
        client_id = uuid.uuid7()
        establishment_id = uuid.uuid7()
        token = create_client_mcp_session_token(
            client_id=client_id,
            establishment_id=establishment_id,
            phone="+5547999998888",
        )

        access_token = await SessionTokenVerifier().verify_token(token)

        assert access_token is not None
        assert access_token.claims == {
            "client_id": str(client_id),
            "establishment_id": str(establishment_id),
            "phone": "+5547999998888",
        }
        assert access_token.subject == str(client_id)

    async def test_recusa_token_malformado(self) -> None:
        assert await SessionTokenVerifier().verify_token("nao-e-um-jwt") is None

    async def test_recusa_token_de_acesso_do_painel(self) -> None:
        """
        Um token do painel não pode virar sessão de cliente: além do `type` diferente,
        ele é assinado com outro segredo.
        """

        painel = create_access_token(TokenIdentity(subject=uuid.uuid7()))

        assert await SessionTokenVerifier().verify_token(painel) is None

    async def test_recusa_token_vazio(self) -> None:
        assert await SessionTokenVerifier().verify_token("") is None
