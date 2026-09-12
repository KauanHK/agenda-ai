"""Composition root: monta as dependências concretas da aplicação.

Só este módulo (e `main.py`) conhece as classes concretas de infraestrutura;
ninguém mais instancia adapter. O `AsyncExitStack` devolvido guarda tudo que
precisa ser fechado no shutdown (clientes HTTP, Redis, saver).

Ordem de construção: Redis → checkpointer → clientes HTTP → sessão → grafo →
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

from src.application.use_cases.handle_incoming_message import HandleIncomingMessage
from src.application.use_cases.open_booking_session import BookingSessionProvider
from src.application.use_cases.reset_conversation import ResetConversation
from src.infrastructure.agendabot.http_client import build_agendabot_client
from src.infrastructure.agendabot.session_issuer import AgendaBotSessionIssuer
from src.infrastructure.agendabot.tool_provider import AgendaBotToolProvider
from src.infrastructure.agent.graph import build_graph
from src.infrastructure.agent.runner import LangGraphAgentRunner
from src.infrastructure.identity.synthetic_phone import SyntheticPhoneResolver
from src.infrastructure.llm.factory import build_chat_model
from src.infrastructure.redis.checkpointer import open_conversation_checkpointer
from src.infrastructure.redis.client import build_redis_client
from src.infrastructure.redis.conversation_history import CheckpointerConversationHistory
from src.infrastructure.redis.session_cache import RedisSessionTokenCache
from src.infrastructure.telegram.client import TelegramMessenger, build_telegram_client
from src.infrastructure.telegram.update_parser import parse_update
from src.infrastructure.telegram.webhook_handler import TelegramWebhookHandler
from src.infrastructure.telegram.webhook_registry import TelegramWebhookRegistry
from src.settings import Settings

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
    establishment_tz = ZoneInfo(settings.agendabot.establishment_timezone)

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

    agendabot_client = await stack.enter_async_context(
        build_agendabot_client(
            base_url=settings.agendabot.api_url,
            service_key=settings.agendabot.service_key.get_secret_value(),
            connect_timeout_seconds=settings.http.connect_timeout_seconds,
            read_timeout_seconds=settings.http.timeout_seconds,
        )
    )
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
        issuer=AgendaBotSessionIssuer(
            agendabot_client,
            establishment_id=settings.agendabot.establishment_id,
            clock=_utc_now,
        ),
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
        clock=lambda: datetime.now(establishment_tz),
    )
    reset_conversation = ResetConversation(CheckpointerConversationHistory(checkpointer))

    webhook_handler = TelegramWebhookHandler(
        parse_update=functools.partial(
            parse_update,
            phone_resolver=phone_resolver,
            max_chars=settings.conversation.max_input_chars,
        ),
        handle_incoming_message=handle_incoming_message,
        reset_conversation=reset_conversation,
        messenger=messenger,
    )
    webhook_secret = settings.telegram.webhook_secret.get_secret_value()
    webhook_registry = TelegramWebhookRegistry(telegram_client, webhook_secret=webhook_secret)
    logger.info("Dependências montadas (estabelecimento %s)", settings.agendabot.establishment_id)

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
