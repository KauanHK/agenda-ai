"""Caso de uso do caminho principal: atender uma mensagem do cliente.

Recebe uma `IncomingMessage` já parseada pelo canal e não devolve nada — o
efeito é a resposta entregue de volta ao canal. A única responsabilidade de
`execute` é garantir que **sempre** sai uma resposta: falhas esperadas
(`AgentError`) viram texto em linguagem natural para o cliente, e quem chama (o
webhook) nunca precisa decidir o que o cliente lê.
"""

import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from src.application.ports.agent_runner import AgentRunnerProtocol
from src.application.ports.messenger import OutboundMessengerProtocol
from src.application.ports.tool_provider import BookingToolProviderProtocol
from src.application.use_cases.open_booking_session import BookingSessionProvider
from src.domain.entities import AgentContext, Contact, ConversationRef, IncomingMessage
from src.domain.exceptions import AgentError

logger = logging.getLogger(__name__)


@dataclass
class _TurnOutcome:
    """Carrega o texto que o cliente vai ler ao fim do turno."""

    text: str = AgentError.user_message


@contextmanager
def _guard_answer(ref: ConversationRef) -> Generator[_TurnOutcome]:
    """Garante que o turno sempre produz um texto para o cliente.

    `AgentError` não sobe: vira o seu `user_message`. Qualquer outra exceção é
    logada com `logger.exception` e cai na frase padrão — o cliente nunca vê
    stacktrace nem detalhe interno. Em ambos os casos a exceção é engolida e
    quem chama lê `outcome.text`.
    """
    outcome = _TurnOutcome()
    try:
        yield outcome
    except AgentError as error:
        logger.warning("Turno falhou para %s: %s", ref.thread_id, error)
        outcome.text = error.user_message
    except Exception:
        logger.exception("Erro inesperado no turno de %s", ref.thread_id)
        outcome.text = AgentError.user_message


class HandleIncomingMessage:
    """Atende uma mensagem do cliente de ponta a ponta."""

    def __init__(
        self,
        session_provider: BookingSessionProvider,
        tool_provider: BookingToolProviderProtocol,
        agent: AgentRunnerProtocol,
        messenger: OutboundMessengerProtocol,
        *,
        clock: Callable[[], datetime],
    ) -> None:
        self._session_provider = session_provider
        self._tool_provider = tool_provider
        self._agent = agent
        self._messenger = messenger
        # Devolve o "agora" *timezone-aware* no fuso do estabelecimento — é o que
        # o system prompt usa para resolver "amanhã", "sexta". Injetado para o
        # teste controlar o tempo sem `freezegun`, como em `BookingSessionProvider`.
        self._clock = clock

    async def execute(self, message: IncomingMessage) -> None:
        """Produz a resposta do turno e a entrega ao canal, sempre.

        `AgentError` não sobe: vira o `user_message` do erro. Um erro inesperado
        é logado com `logger.exception` e responde com a frase padrão — o cliente
        nunca vê stacktrace nem detalhe interno.
        """
        ref = ConversationRef(
            channel=message.contact.channel,
            channel_user_id=message.contact.channel_user_id,
        )
        await self._signal_typing(contact=message.contact)
        with _guard_answer(ref) as outcome:
            outcome.text = await self._produce_answer(message, ref)
        await self._messenger.send_text(message.contact, outcome.text)

    async def _produce_answer(self, message: IncomingMessage, ref: ConversationRef) -> str:
        """Abre a sessão, carrega as tools e roda o turno do agente."""
        session = await self._session_provider.for_contact(message.contact)
        tools = await self._tool_provider.tools_for(session.token)
        answer = await self._agent.run(
            conversation=ref,
            user_text=message.text,
            tools=tools,
            context=AgentContext(
                client_name=session.client_name,
                now=self._clock(),
                is_new_client=session.is_new_client,
            ),
        )
        return answer.text

    async def _signal_typing(self, contact: Contact) -> None:
        """Sinaliza "digitando" sem deixar uma falha aí impedir a resposta."""
        try:
            await self._messenger.signal_typing(contact)
        except Exception:
            logger.debug("signal_typing falhou; seguindo sem o indicador", exc_info=True)
