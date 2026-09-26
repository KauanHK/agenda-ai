"""O roteador dedicado: de um update cru do Telegram até o caso de uso certo.

Fica em `infrastructure` porque conhece o formato do update e a convenção de
comando do Telegram. É montado pelo composition root e exposto ao webhook como
uma única coroutine — a rota HTTP não decide nada, só responde `200` e delega.
"""

import logging
from collections.abc import Callable, Mapping
from typing import Any

from app.modules.agent.adapters.telegram.commands import (
    RESET_COMMANDS,
    RESET_MESSAGE,
    WELCOME_MESSAGE,
    match_command,
)
from app.modules.agent.application.ports.messenger import OutboundMessengerProtocol
from app.modules.agent.application.use_cases.handle_incoming_message import (
    HandleIncomingMessage,
)
from app.modules.agent.application.use_cases.reset_conversation import ResetConversation
from app.modules.agent.domain.entities import ConversationRef, IncomingMessage
from app.modules.agent.domain.exceptions import AgentError
from app.modules.agent.logging_config import bind_thread_id

logger = logging.getLogger(__name__)

ParseUpdate = Callable[[Mapping[str, Any]], IncomingMessage | None]

_FAILURE_MSG = "Falha ao processar um update do Telegram"


class TelegramWebhookHandler:
    """Parseia o update e o encaminha para um comando ou para o agente."""

    def __init__(
        self,
        *,
        parse_update: ParseUpdate,
        handle_incoming_message: HandleIncomingMessage,
        reset_conversation: ResetConversation,
        messenger: OutboundMessengerProtocol,
    ) -> None:
        self._parse_update = parse_update
        self._handle_incoming_message = handle_incoming_message
        self._reset_conversation = reset_conversation
        self._messenger = messenger

    async def handle_update(self, payload: Mapping[str, Any]) -> None:
        """Trata um update do webhook. Nunca levanta: o webhook já respondeu `200`."""
        parsed = self._parse(payload)
        if parsed is None:
            return
        message, ref = parsed

        # Todo `logger.*` deste turno — inclusive o de falha — sai carimbado com
        # o `thread_id`, por isso o `try` do turno fica dentro do `bind`.
        with bind_thread_id(ref.thread_id):
            try:
                await self._route(message, ref)
            except Exception:
                logger.exception(_FAILURE_MSG)

    def _parse(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[IncomingMessage, ConversationRef] | None:
        """Extrai a mensagem e o `ConversationRef` do update, ou `None` se não houver
        mensagem tratável. Nunca levanta: registra a falha e devolve `None`."""
        try:
            message = self._parse_update(payload)
            if message is None:
                return None
            ref = ConversationRef(
                channel=message.contact.channel,
                channel_user_id=message.contact.channel_user_id,
            )
        except Exception:
            logger.exception(_FAILURE_MSG)
            return None
        return message, ref

    async def _route(self, message: IncomingMessage, ref: ConversationRef) -> None:
        command = match_command(message.text)
        if command in RESET_COMMANDS:
            await self._run_reset(message, ref, command)
            return
        await self._handle_incoming_message.execute(message)

    async def _run_reset(
        self, message: IncomingMessage, ref: ConversationRef, command: str | None
    ) -> None:
        """Limpa o histórico e responde com o texto fixo do comando."""
        try:
            await self._reset_conversation.execute(ref)
        except AgentError as error:
            await self._messenger.send_text(message.contact, error.user_message)
            return
        reply = WELCOME_MESSAGE if command == "start" else RESET_MESSAGE
        await self._messenger.send_text(message.contact, reply)
