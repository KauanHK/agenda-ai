"""Smoke test manual da integração com o AgendaBot (Etapas 2 e 3 do roadmap).

Roda contra o ambiente real, lendo as credenciais do `.env`. Não faz parte da
suíte automatizada: é o que responde "o contrato mudou?" sem mock.

Faz o caminho inteiro da sessão: emite um `session_token` real do estabelecimento
fixo, abre a conexão MCP autenticada com esse token e lista as tools publicadas
pelo servidor, com seus schemas de argumentos.

Uso:

    uv run python -m scripts.agent.smoke_mcp
    uv run python -m scripts.agent.smoke_mcp --chat-id 12345 --name "Kauan"
    uv run python -m scripts.agent.smoke_mcp --phone 554792277579 --show-token
    uv run python -m scripts.agent.smoke_mcp --full-schema
"""

import argparse
import asyncio
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from app.modules.agent.adapters.agendabot.http_client import build_agendabot_client
from app.modules.agent.adapters.agendabot.session_issuer import AgendaBotSessionIssuer
from app.modules.agent.adapters.agendabot.tool_provider import AgendaBotToolProvider
from app.modules.agent.adapters.identity.synthetic_phone import SyntheticPhoneResolver
from app.modules.agent.domain.entities import Channel
from app.modules.agent.domain.exceptions import AgentError
from app.modules.agent.settings import Settings


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emite uma sessão real no AgendaBot e lista as tools do MCP."
    )
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
    parser.add_argument(
        "--full-schema",
        action="store_true",
        help="imprime o schema de argumentos de cada tool em JSON completo",
    )
    return parser.parse_args()


def _mask(token: str) -> str:
    if len(token) <= 18:
        return f"*** ({len(token)} chars)"
    return f"{token[:12]}…{token[-6:]} ({len(token)} chars)"


def _first_line(text: str | None) -> str:
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return "(sem descrição)"


def _print_tools(tools: Sequence[Any], *, full_schema: bool) -> None:
    print(f"\nTools carregadas: {len(tools)}")
    for tool in tools:
        print(f"\n  {tool.name}")
        print(f"    {_first_line(tool.description)}")
        args: dict[str, Any] = tool.args
        if not args:
            print("    args: (nenhum)")
        elif full_schema:
            for line in json.dumps(args, indent=2, ensure_ascii=False).splitlines():
                print(f"    {line}")
        else:
            rendered = ", ".join(name + _type_hint(spec) for name, spec in args.items())
            print(f"    args: {rendered}")


def _type_hint(spec: dict[str, Any]) -> str:
    kind = spec.get("type", "?")
    fmt = spec.get("format")
    return f": {kind} ({fmt})" if fmt else f": {kind}"


async def _run(args: argparse.Namespace, settings: Settings) -> None:
    if args.phone is not None:
        phone = str(args.phone)
    else:
        resolver = SyntheticPhoneResolver(settings.identity.synthetic_phone_prefix)
        phone = resolver.resolve(Channel.TELEGRAM, str(args.chat_id))

    print(f"Estabelecimento : {settings.agendabot.establishment_id}")
    print(f"API             : {settings.agendabot.api_url}")
    print(f"MCP             : {settings.agendabot.mcp_url}")
    print(f"Telefone        : {phone}")
    print(f"Nome            : {args.name}")
    print("Emitindo sessão...\n")

    async with build_agendabot_client(
        base_url=settings.agendabot.api_url,
        service_key=settings.agendabot.service_key.get_secret_value(),
        connect_timeout_seconds=settings.http.connect_timeout_seconds,
        read_timeout_seconds=settings.http.timeout_seconds,
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

    print("\nAbrindo conexão MCP e carregando as tools...")
    provider = AgendaBotToolProvider(
        mcp_url=settings.agendabot.mcp_url,
        timeout_seconds=settings.http.mcp_timeout_seconds,
    )
    tools = await provider.tools_for(session.token)
    _print_tools(tools, full_schema=args.full_schema)


def main() -> int:
    args = _parse_args()
    try:
        settings = Settings()
    except ValidationError as error:
        print("Configuração inválida — preencha o `.env` (veja `.env.example`):\n")
        print(error)
        return 2

    if not settings.agendabot.service_key.get_secret_value():
        print("AGENT_AGENDABOT__SERVICE_KEY está vazia no `.env`: a emissão vai falhar com 401.\n")

    try:
        asyncio.run(_run(args, settings))
    except AgentError as error:
        print(f"\nFalha no smoke test: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
