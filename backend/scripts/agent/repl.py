"""REPL do agente no terminal — o agendamento de ponta a ponta, sem Telegram.

Emite a sessão real do cliente, carrega as tools do MCP e roda o grafo turno a
turno contra o LLM configurado. É o que fecha a Etapa 4 do roadmap: uma conversa
que marca, consulta, reagenda e cancela sem nenhum canal envolvido.

Roda à mão, contra o ambiente real, lendo o `.env`. Não faz parte da suíte.

Uso:

    uv run python -m scripts.agent.repl --establishment-id <uuid>
    uv run python -m scripts.agent.repl --establishment-id <uuid> --chat-id 12345 --name "Kauan"
    uv run python -m scripts.agent.repl --establishment-id <uuid> --memory  # sem Redis

O estabelecimento precisa ter um bot conectado: o fuso vem do diretório de canais.

A conversa fica presa a `--chat-id`: para recomeçar do zero, rode com outra.
`/sair` (ou Ctrl-D) encerra.
"""

import argparse
import asyncio
import contextlib
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import ValidationError

from app.core.db.session import db
from app.modules.agent.adapters.booking.session_issuer import InProcessSessionIssuer
from app.modules.agent.adapters.channels.telegram_directory import (
    DbTelegramChannelDirectory,
)
from app.modules.agent.adapters.identity.synthetic_phone import SyntheticPhoneResolver
from app.modules.agent.adapters.langgraph.graph import build_graph
from app.modules.agent.adapters.langgraph.runner import LangGraphAgentRunner
from app.modules.agent.adapters.llm.factory import build_chat_model
from app.modules.agent.adapters.mcp_client.tool_provider import AgendaBotToolProvider
from app.modules.agent.adapters.redis.checkpointer import open_conversation_checkpointer
from app.modules.agent.adapters.redis.client import build_redis_client
from app.modules.agent.adapters.redis.session_cache import RedisSessionTokenCache
from app.modules.agent.application.ports.session_cache import SessionTokenCacheProtocol
from app.modules.agent.application.use_cases.open_booking_session import (
    BookingSessionProvider,
)
from app.modules.agent.domain.entities import (
    AgentContext,
    BookingSession,
    Channel,
    Contact,
    ConversationRef,
    Establishment,
)
from app.modules.agent.domain.exceptions import AgentError
from app.modules.agent.settings import Settings

TurnHandler = Callable[[Contact, ConversationRef, str], Awaitable[str]]


class _NoChannelError(AgentError):
    """O estabelecimento não tem bot conectado (ou não atende)."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--establishment-id",
        type=uuid.UUID,
        required=True,
        help="estabelecimento atendido (precisa ter um bot conectado)",
    )
    parser.add_argument(
        "--chat-id",
        default="repl",
        help="id de chat para a thread e o telefone sintético (default: repl)",
    )
    parser.add_argument(
        "--name",
        default="REPL",
        help="nome enviado na emissão da sessão (default: REPL)",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="usa checkpointer e cache de sessão em memória, sem Redis",
    )
    return parser.parse_args()


class _NullSessionCache:
    """Cache que nunca guarda nada: força reemissão a cada turno. Implementa a porta."""

    async def get(self, establishment_id: uuid.UUID, phone: str) -> BookingSession | None:
        return None

    async def put(self, session: BookingSession) -> None:
        return None


def _now_utc() -> datetime:
    return datetime.now(UTC)


@contextlib.asynccontextmanager
async def _checkpointer(
    settings: Settings, *, in_memory: bool
) -> AsyncIterator[BaseCheckpointSaver[Any]]:
    """Abre o checkpointer: Redis por padrão, em memória com `--memory`."""
    if in_memory:
        yield InMemorySaver()
        return
    async with open_conversation_checkpointer(
        settings.redis.url,
        ttl_minutes=settings.conversation.ttl_minutes,
    ) as saver:
        yield saver


def _session_cache(
    settings: Settings,
    stack: contextlib.AsyncExitStack,
    *,
    in_memory: bool,
) -> SessionTokenCacheProtocol:
    """Cache do token de sessão: Redis por padrão, no-op com `--memory`."""
    if in_memory:
        return _NullSessionCache()
    redis_client = build_redis_client(settings.redis.url)
    stack.push_async_callback(redis_client.aclose)
    return RedisSessionTokenCache(
        redis_client,
        clock=_now_utc,
        refresh_margin_seconds=settings.conversation.session_refresh_margin_seconds,
    )


async def _establishment(establishment_id: uuid.UUID) -> Establishment:
    """O estabelecimento com o fuso, pelo diretório de canais (exige `db.init()`)."""
    channel = await DbTelegramChannelDirectory().get(establishment_id)
    if channel is None:
        raise _NoChannelError(f"O estabelecimento {establishment_id} não tem bot conectado.")
    return channel.establishment


async def _build_turn_handler(
    settings: Settings,
    stack: contextlib.AsyncExitStack,
    establishment: Establishment,
    *,
    in_memory: bool,
) -> TurnHandler:
    """Monta as dependências reais e devolve uma função que roda um turno."""
    session_provider = BookingSessionProvider(
        phone_resolver=SyntheticPhoneResolver(settings.identity.synthetic_phone_prefix),
        issuer=InProcessSessionIssuer(clock=_now_utc),
        cache=_session_cache(settings, stack, in_memory=in_memory),
        clock=_now_utc,
        refresh_margin_seconds=settings.conversation.session_refresh_margin_seconds,
    )
    tool_provider = AgendaBotToolProvider(
        mcp_url=settings.agendabot.mcp_url,
        timeout_seconds=settings.http.mcp_timeout_seconds,
    )
    checkpointer = await stack.enter_async_context(_checkpointer(settings, in_memory=in_memory))
    runner = LangGraphAgentRunner(
        build_graph(
            build_chat_model(settings.llm),
            checkpointer=checkpointer,
            history_limit=settings.conversation.max_history_turns,
        ),
        max_agent_steps=settings.conversation.max_agent_steps,
    )
    async def handle(contact: Contact, ref: ConversationRef, text: str) -> str:
        session = await session_provider.for_contact(contact, establishment.id)
        tools = await tool_provider.tools_for(session.token)
        answer = await runner.run(
            conversation=ref,
            user_text=text,
            tools=tools,
            context=AgentContext(
                client_name=session.client_name,
                now=datetime.now(establishment.timezone),
                is_new_client=session.is_new_client,
            ),
        )
        return answer.text

    return handle


async def _loop(
    handle: TurnHandler, establishment: Establishment, args: argparse.Namespace
) -> None:
    chat_id = str(args.chat_id)
    ref = ConversationRef(
        channel=Channel.TELEGRAM,
        establishment_id=establishment.id,
        channel_user_id=chat_id,
    )
    contact = Contact(
        channel=Channel.TELEGRAM,
        channel_user_id=chat_id,
        display_name=str(args.name),
        phone="",  # o SyntheticPhoneResolver deriva do channel_user_id.
    )

    print("Agente pronto. Escreva uma mensagem (/sair encerra).\n")
    while True:
        try:
            text = (await asyncio.to_thread(input, "você> ")).strip()
        except EOFError, KeyboardInterrupt:
            print()
            return
        if not text:
            continue
        if text == "/sair":
            return
        try:
            answer = await handle(contact, ref, text)
        except AgentError as error:
            print(f"agente> {error.user_message}")
            if error.__cause__ is not None:
                print(f"        (debug: {error.__cause__!r})")
            print()
            continue
        print(f"agente> {answer}\n")


async def _run(args: argparse.Namespace, settings: Settings) -> None:
    async with contextlib.AsyncExitStack() as stack:
        db.init()
        stack.push_async_callback(db.close)
        establishment = await _establishment(args.establishment_id)
        handle = await _build_turn_handler(
            settings, stack, establishment, in_memory=args.memory
        )
        await _loop(handle, establishment, args)


def main() -> int:
    args = _parse_args()
    try:
        settings = Settings()
    except ValidationError as error:
        print("Configuração inválida — preencha o `.env` (veja `.env.example`):\n")
        print(error)
        return 2
    try:
        asyncio.run(_run(args, settings))
    except AgentError as error:
        print(f"\nFalha: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
