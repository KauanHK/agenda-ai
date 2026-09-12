"""REPL do agente no terminal — o agendamento de ponta a ponta, sem Telegram.

Emite a sessão real do cliente, carrega as tools do MCP e roda o grafo turno a
turno contra o LLM configurado. É o que fecha a Etapa 4 do roadmap: uma conversa
que marca, consulta, reagenda e cancela sem nenhum canal envolvido.

Roda à mão, contra o ambiente real, lendo o `.env`. Não faz parte da suíte.

Uso:

    uv run python -m scripts.repl
    uv run python -m scripts.repl --chat-id 12345 --name "Kauan"
    uv run python -m scripts.repl --memory      # checkpointer e cache sem Redis

A conversa fica presa a `--chat-id`: para recomeçar do zero, rode com outra.
`/sair` (ou Ctrl-D) encerra.
"""

import argparse
import asyncio
import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import ValidationError

from src.application.ports.session_cache import SessionTokenCacheProtocol
from src.application.use_cases.open_booking_session import BookingSessionProvider
from src.domain.entities import AgentContext, BookingSession, Channel, Contact, ConversationRef
from src.domain.exceptions import AgentError
from src.infrastructure.agendabot.http_client import build_agendabot_client
from src.infrastructure.agendabot.session_issuer import AgendaBotSessionIssuer
from src.infrastructure.agendabot.tool_provider import AgendaBotToolProvider
from src.infrastructure.agent.graph import build_graph
from src.infrastructure.agent.runner import LangGraphAgentRunner
from src.infrastructure.identity.synthetic_phone import SyntheticPhoneResolver
from src.infrastructure.llm.factory import build_chat_model
from src.infrastructure.redis.checkpointer import open_conversation_checkpointer
from src.infrastructure.redis.client import build_redis_client
from src.infrastructure.redis.session_cache import RedisSessionTokenCache
from src.settings import Settings

TurnHandler = Callable[[Contact, ConversationRef, str], Awaitable[str]]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    async def get(self, phone: str) -> BookingSession | None:
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


async def _build_turn_handler(
    settings: Settings,
    stack: contextlib.AsyncExitStack,
    *,
    in_memory: bool,
) -> TurnHandler:
    """Monta as dependências reais e devolve uma função que roda um turno."""
    client = await stack.enter_async_context(
        build_agendabot_client(
            base_url=settings.agendabot.api_url,
            service_key=settings.agendabot.service_key.get_secret_value(),
            connect_timeout_seconds=settings.http.connect_timeout_seconds,
            read_timeout_seconds=settings.http.timeout_seconds,
        )
    )
    session_provider = BookingSessionProvider(
        phone_resolver=SyntheticPhoneResolver(settings.identity.synthetic_phone_prefix),
        issuer=AgendaBotSessionIssuer(
            client,
            establishment_id=settings.agendabot.establishment_id,
            clock=_now_utc,
        ),
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
    tz = ZoneInfo(settings.agendabot.establishment_timezone)

    async def handle(contact: Contact, ref: ConversationRef, text: str) -> str:
        session = await session_provider.for_contact(contact)
        tools = await tool_provider.tools_for(session.token)
        answer = await runner.run(
            conversation=ref,
            user_text=text,
            tools=tools,
            context=AgentContext(
                client_name=session.client_name,
                now=datetime.now(tz),
                is_new_client=session.is_new_client,
            ),
        )
        return answer.text

    return handle


async def _loop(handle: TurnHandler, args: argparse.Namespace) -> None:
    chat_id = str(args.chat_id)
    ref = ConversationRef(channel=Channel.TELEGRAM, channel_user_id=chat_id)
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
        handle = await _build_turn_handler(settings, stack, in_memory=args.memory)
        await _loop(handle, args)


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
