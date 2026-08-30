"""O roteador dedicado: de um update cru do Telegram até o caso de uso certo.

Fica em `infrastructure` porque conhece o formato do update e a convenção de
comando do Telegram. É montado pelo composition root e exposto ao webhook como
uma única coroutine — a rota HTTP não decide nada, só responde `200` e delega.
"""

import logging
from collections.abc import Callable, Mapping
from typing import Any

from src.application.ports.messenger import OutboundMessengerProtocol
from src.application.use_cases.handle_incoming_message import HandleIncomingMessage
from src.application.use_cases.reset_conversation import ResetConversation
from src.domain.entities import ConversationRef, IncomingMessage
from src.domain.exceptions import AgentError
from src.infrastructure.telegram.commands import (
    RESET_COMMANDS,
    RESET_MESSAGE,
    WELCOME_MESSAGE,
    match_command,
)

logger = logging.getLogger(__name__)

ParseUpdate = Callable[[Mapping[str, Any]], IncomingMessage | None]


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
        try:
            await self._route(payload)
        except Exception:
            logger.exception("Falha ao processar um update do Telegram")

    async def _route(self, payload: Mapping[str, Any]) -> None:
        message = self._parse_update(payload)
        if message is None:
            return
        command = match_command(message.text)
        if command in RESET_COMMANDS:
            await self._run_reset(message, command)
            return
        await self._handle_incoming_message.execute(message)

    async def _run_reset(self, message: IncomingMessage, command: str | None) -> None:
        """Limpa o histórico e responde com o texto fixo do comando."""
        ref = ConversationRef(message.contact.channel, message.contact.channel_user_id)
        try:
            await self._reset_conversation.execute(ref)
        except AgentError as error:
            await self._messenger.send_text(message.contact, error.user_message)
            return
        reply = WELCOME_MESSAGE if command == "start" else RESET_MESSAGE
        await self._messenger.send_text(message.contact, reply)
