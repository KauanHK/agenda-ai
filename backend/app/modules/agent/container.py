"""Composition root: monta as dependências concretas da aplicação.

Só este módulo (e `main.py`) conhece as classes concretas de infraestrutura;
ninguém mais instancia adapter. O `AsyncExitStack` devolvido guarda tudo que
precisa ser fechado no shutdown (pool do banco, clientes HTTP, Redis, saver).

Ordem de construção: banco → Redis → checkpointer → cliente HTTP → sessão → grafo →
adapters do Telegram → casos de uso → roteador do webhook.
"""

import asyncio
import functools
import logging
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

from redis.exceptions import RedisError

from app.core.db.session import db
from app.modules.agent.adapters.booking.session_issuer import InProcessSessionIssuer
from app.modules.agent.adapters.identity.synthetic_phone import SyntheticPhoneResolver
from app.modules.agent.adapters.langgraph.graph import build_graph
from app.modules.agent.adapters.langgraph.runner import LangGraphAgentRunner
from app.modules.agent.adapters.llm.factory import build_chat_model
from app.modules.agent.adapters.mcp_client.tool_provider import AgendaBotToolProvider
from app.modules.agent.adapters.redis.checkpointer import open_conversation_checkpointer
from app.modules.agent.adapters.redis.client import build_redis_client
from app.modules.agent.adapters.redis.conversation_history import (
    CheckpointerConversationHistory,
)
from app.modules.agent.adapters.redis.session_cache import RedisSessionTokenCache
from app.modules.agent.adapters.telegram.client import (
    TelegramMessenger,
    build_telegram_client,
)
from app.modules.agent.adapters.telegram.update_parser import parse_update
from app.modules.agent.adapters.telegram.webhook_handler import TelegramWebhookHandler
from app.modules.agent.adapters.telegram.webhook_registry import TelegramWebhookRegistry
from app.modules.agent.application.use_cases.handle_incoming_message import (
    HandleIncomingMessage,
)
from app.modules.agent.application.use_cases.open_booking_session import (
    BookingSessionProvider,
)
from app.modules.agent.application.use_cases.reset_conversation import ResetConversation
from app.modules.agent.domain.entities import Establishment
from app.modules.agent.settings import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Container:
    """As dependências prontas que a interface HTTP consome."""

    handle_update: Callable[[Mapping[str, Any]], Coroutine[Any, Any, None]]
    webhook_secret: str
    check_readiness: Callable[[], Awaitable[dict[str, str]]]
    """Relatório de *readiness*: `{"redis": "ok"}` ou `{"redis": "down"}`."""
    admin_token: str
    """Bearer token das rotas `/admin`."""
    register_webhook: Callable[[str, bool], Awaitable[dict[str, Any]]]
    """`(base_url, drop_pending_updates)` → `getWebhookInfo` após o `setWebhook`."""
    get_webhook_info: Callable[[], Awaitable[dict[str, Any]]]
    """`getWebhookInfo` com o segredo mascarado."""


_READINESS_REDIS_TIMEOUT_SECONDS = 2.0


async def build_container(settings: Settings) -> tuple[Container, AsyncExitStack]:
    """Constrói as dependências e devolve o stack que as fecha no shutdown."""
    stack = AsyncExitStack()
    try:
        container = await _wire(settings=settings, stack=stack)
    except BaseException:
        await stack.aclose()
        raise
    return container, stack


def _utc_now() -> datetime:
    return datetime.now(UTC)


async def _wire(settings: Settings, stack: AsyncExitStack) -> Container:
    """Instancia e liga tudo, registrando no `stack` o que precisa ser fechado."""
    # O único lugar que ainda sabe que existe um estabelecimento só: todo o resto
    # recebe o estabelecimento pela mensagem.
    establishment = Establishment(
        id=settings.agendabot.establishment_id,
        timezone=ZoneInfo(settings.agendabot.establishment_timezone),
    )

    db.init()
    stack.push_async_callback(db.close)

    checkpointer = await stack.enter_async_context(
        open_conversation_checkpointer(
            settings.redis.url,
            ttl_minutes=settings.conversation.ttl_minutes,
        )
    )
    redis_client = build_redis_client(settings.redis.url)
    stack.push_async_callback(redis_client.aclose)

    async def check_readiness() -> dict[str, str]:
        """`PING` no Redis com timeout curto; nunca levanta, só relata."""
        try:
            ping = cast("Awaitable[object]", redis_client.ping())
            await asyncio.wait_for(ping, timeout=_READINESS_REDIS_TIMEOUT_SECONDS)
        except RedisError, OSError, TimeoutError:
            return {"redis": "down"}
        return {"redis": "ok"}

    telegram_client = await stack.enter_async_context(
        build_telegram_client(
            api_root=settings.telegram.api_root,
            bot_token=settings.telegram.bot_token.get_secret_value(),
            connect_timeout_seconds=settings.http.connect_timeout_seconds,
            read_timeout_seconds=settings.http.telegram_read_timeout_seconds,
        )
    )

    phone_resolver = SyntheticPhoneResolver(settings.identity.synthetic_phone_prefix)
    session_provider = BookingSessionProvider(
        phone_resolver=phone_resolver,
        issuer=InProcessSessionIssuer(clock=_utc_now),
        cache=RedisSessionTokenCache(
            redis_client,
            clock=_utc_now,
            refresh_margin_seconds=settings.conversation.session_refresh_margin_seconds,
        ),
        clock=_utc_now,
        refresh_margin_seconds=settings.conversation.session_refresh_margin_seconds,
    )
    tool_provider = AgendaBotToolProvider(
        mcp_url=settings.agendabot.mcp_url,
        timeout_seconds=settings.http.mcp_timeout_seconds,
    )

    runner = LangGraphAgentRunner(
        build_graph(
            build_chat_model(settings.llm),
            checkpointer=checkpointer,
            history_limit=settings.conversation.max_history_turns,
        ),
        max_agent_steps=settings.conversation.max_agent_steps,
    )

    messenger = TelegramMessenger(telegram_client)
    handle_incoming_message = HandleIncomingMessage(
        session_provider,
        tool_provider,
        runner,
        messenger,
        clock=_utc_now,
    )
    reset_conversation = ResetConversation(CheckpointerConversationHistory(checkpointer))

    webhook_handler = TelegramWebhookHandler(
        parse_update=functools.partial(
            parse_update,
            phone_resolver=phone_resolver,
            establishment=establishment,
            max_chars=settings.conversation.max_input_chars,
        ),
        handle_incoming_message=handle_incoming_message,
        reset_conversation=reset_conversation,
        messenger=messenger,
    )
    webhook_secret = settings.telegram.webhook_secret.get_secret_value()
    webhook_registry = TelegramWebhookRegistry(telegram_client, webhook_secret=webhook_secret)
    logger.info("Dependências montadas (estabelecimento %s)", establishment.id)

    return Container(
        handle_update=webhook_handler.handle_update,
        webhook_secret=webhook_secret,
        check_readiness=check_readiness,
        admin_token=settings.telegram.admin_token.get_secret_value(),
        register_webhook=lambda base_url, drop_pending_updates: webhook_registry.register(
            base_url, drop_pending_updates=drop_pending_updates
        ),
        get_webhook_info=webhook_registry.info,
    )
