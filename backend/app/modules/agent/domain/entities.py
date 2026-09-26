"""Entidades do agente.

Camada pura: só `dataclasses`, `enum`, `datetime`, `uuid`, `zoneinfo`. Nenhum I/O, nenhuma
dependência externa. Tudo imutável (`frozen=True`).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo


class Channel(StrEnum):
    """Canal por onde o cliente conversa com o agente."""

    TELEGRAM = "telegram"


@dataclass(frozen=True, slots=True)
class Establishment:
    """O que o agente precisa saber do estabelecimento que atende a conversa."""

    id: uuid.UUID
    timezone: ZoneInfo
    """Fuso em que o cliente fala de "amanhã" e "sexta"."""


@dataclass(frozen=True, slots=True)
class TelegramChannel:
    """O bot do Telegram que atende um estabelecimento."""

    establishment: Establishment
    bot_token: str = field(repr=False)
    webhook_secret: str = field(repr=False)
    """Quem tem o segredo forja updates; nenhum dos dois pode aparecer em log."""


@dataclass(frozen=True, slots=True)
class Contact:
    """Quem está conversando, do ponto de vista do agente."""

    channel: Channel
    channel_user_id: str
    display_name: str | None
    phone: str


@dataclass(frozen=True, slots=True)
class IncomingMessage:
    """Uma mensagem de texto recebida de um canal."""

    establishment: Establishment
    contact: Contact
    text: str
    channel_message_id: str
    received_at: datetime

    @property
    def conversation(self) -> ConversationRef:
        """A conversa a que a mensagem pertence: canal, estabelecimento e usuário."""
        return ConversationRef(
            channel=self.contact.channel,
            establishment_id=self.establishment.id,
            channel_user_id=self.contact.channel_user_id,
        )


@dataclass(frozen=True, slots=True)
class AgentAnswer:
    """O que o agente decidiu responder ao final de um turno."""

    text: str
    tool_calls_made: int
    """Observabilidade; não vai para o usuário."""


@dataclass(frozen=True, slots=True)
class AgentContext:
    """O contexto do turno que o system prompt precisa e não vem do histórico.

    O nome do cliente e o "cliente novo" saem da sessão emitida, não das
    mensagens: uma thread que expirou no Redis começa do zero, mas o cliente
    continua sendo o mesmo do AgendaBot.
    """

    client_name: str
    now: datetime
    """Data e hora atuais, *timezone-aware*, no fuso do estabelecimento."""
    is_new_client: bool


@dataclass(frozen=True, slots=True)
class BookingSession:
    """A sessão autenticada do cliente no AgendaBot."""

    token: str
    establishment_id: uuid.UUID
    """Estabelecimento da sessão; junto com o telefone, é a chave do cache."""
    phone: str
    """Telefone canônico (E.164 sem `+`) que originou a sessão."""
    client_id: uuid.UUID
    client_name: str
    expires_at: datetime
    is_new_client: bool

    def is_valid_at(self, moment: datetime) -> bool:
        """Diz se a sessão ainda vale no instante dado.

        Na borda exata da expiração a sessão já **não** vale.
        """
        return moment < self.expires_at


@dataclass(frozen=True, slots=True)
class ConversationRef:
    """Identifica a conversa: a thread no checkpointer e o destino da resposta."""

    channel: Channel
    establishment_id: uuid.UUID
    channel_user_id: str

    @property
    def thread_id(self) -> str:
        """A chave estável da thread: `telegram:{establishment_id}:123456`.

        O canal impede que a thread do Telegram colida com a de outro canal. O
        estabelecimento impede que o mesmo usuário, falando com os bots de dois
        estabelecimentos, misture os históricos: no Telegram, o `chat_id` de uma
        conversa privada é o id do usuário, igual em todos os bots.
        """
        return f"{self.channel.value}:{self.establishment_id}:{self.channel_user_id}"
