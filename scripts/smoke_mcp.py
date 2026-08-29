"""Smoke test manual da emissão de sessão no AgendaBot (Etapa 2 do roadmap).

Roda contra o ambiente real, lendo as credenciais do `.env`. Não faz parte da
suíte automatizada: é o que responde "o contrato da sessão mudou?" sem mock.

Uso:

    uv run python -m scripts.smoke_mcp
    uv run python -m scripts.smoke_mcp --chat-id 12345 --name "Kauan"
    uv run python -m scripts.smoke_mcp --phone 554792277579 --show-token

A Etapa 3 completa este script com a conexão MCP e a listagem das tools.
"""

import argparse
import asyncio
from datetime import UTC, datetime

from pydantic import ValidationError

from src.domain.entities import Channel
from src.domain.exceptions import AgentError
from src.infrastructure.agendabot.http_client import build_agendabot_client
from src.infrastructure.agendabot.session_issuer import AgendaBotSessionIssuer
from src.infrastructure.identity.synthetic_phone import SyntheticPhoneResolver
from src.settings import Settings


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emite uma sessão real no AgendaBot.")
    parser.add_argument(
        "--chat-id",
        default="smoke-mcp",
        help="id de chat para derivar o telefone sintético (default: smoke-mcp)",
    )
    parser.add_argument(
        "--phone",
        default=None,
        help="telefone E.164 sem '+' a usar diretamente, ignorando --chat-id",
    )
    parser.add_argument(
        "--name",
        default="Smoke MCP",
        help="nome enviado na emissão da sessão (default: 'Smoke MCP')",
    )
    parser.add_argument(
        "--show-token",
        action="store_true",
        help="imprime o session_token inteiro em vez de mascará-lo",
    )
    return parser.parse_args()


def _mask(token: str) -> str:
    if len(token) <= 18:
        return f"*** ({len(token)} chars)"
    return f"{token[:12]}…{token[-6:]} ({len(token)} chars)"


async def _run(args: argparse.Namespace, settings: Settings) -> None:
    if args.phone is not None:
        phone = str(args.phone)
    else:
        resolver = SyntheticPhoneResolver(settings.identity.synthetic_phone_prefix)
        phone = resolver.resolve(Channel.TELEGRAM, str(args.chat_id))

    print(f"Estabelecimento : {settings.agendabot.establishment_id}")
    print(f"API             : {settings.agendabot.api_url}")
    print(f"Telefone        : {phone}")
    print(f"Nome            : {args.name}")
    print("Emitindo sessão...\n")

    async with build_agendabot_client(
        base_url=settings.agendabot.api_url,
        service_key=settings.agendabot.service_key.get_secret_value(),
        timeout_seconds=settings.http.timeout_seconds,
    ) as client:
        issuer = AgendaBotSessionIssuer(
            client,
            establishment_id=settings.agendabot.establishment_id,
            clock=lambda: datetime.now(UTC),
        )
        session = await issuer.issue(phone, str(args.name))

    token = session.token if args.show_token else _mask(session.token)
    print("Sessão emitida:")
    print(f"  token         : {token}")
    print(f"  client_id     : {session.client_id}")
    print(f"  client_name   : {session.client_name}")
    print(f"  is_new_client : {session.is_new_client}")
    print(f"  expires_at    : {session.expires_at.isoformat()}")


def main() -> int:
    args = _parse_args()
    try:
        settings = Settings()
    except ValidationError as error:
        print("Configuração inválida — preencha o `.env` (veja `.env.example`):\n")
        print(error)
        return 2

    if not settings.agendabot.service_key.get_secret_value():
        print("AGENDABOT__SERVICE_KEY está vazia no `.env`: a emissão vai falhar com 401.\n")

    try:
        asyncio.run(_run(args, settings))
    except AgentError as error:
        print(f"\nFalha ao emitir a sessão: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
