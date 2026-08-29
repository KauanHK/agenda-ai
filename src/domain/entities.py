"""Entidades do agente.

Camada pura: só `dataclasses`, `enum`, `datetime`, `uuid`. Nenhum I/O, nenhuma
dependência externa. Tudo imutável (`frozen=True`).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Channel(StrEnum):
    """Canal por onde o cliente conversa com o agente."""

    TELEGRAM = "telegram"


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

    contact: Contact
    text: str
    channel_message_id: str
    received_at: datetime


@dataclass(frozen=True, slots=True)
class AgentAnswer:
    """O que o agente decidiu responder ao final de um turno."""

    text: str
    tool_calls_made: int
    """Observabilidade; não vai para o usuário."""


@dataclass(frozen=True, slots=True)
class BookingSession:
    """A sessão autenticada do cliente no AgendaBot."""

    token: str
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
    """Identifica a thread de conversa no checkpointer."""

    channel: Channel
    channel_user_id: str

    @property
    def thread_id(self) -> str:
        """A chave estável da thread: `telegram:123456`.

        O canal faz parte da chave: é ele que impede que a thread do Telegram
        colida com a de outro canal quando ele entrar.
        """
        return f"{self.channel.value}:{self.channel_user_id}"
