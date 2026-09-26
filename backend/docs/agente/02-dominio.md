# 02 — Domínio

Camada pura: só `dataclasses`, `enum`, `datetime`, `uuid`. Nenhum I/O, nenhuma
dependência externa. Tudo imutável (`frozen=True`).

## Entidades

`app/modules/agent/domain/entities.py`

```python
@dataclass(frozen=True, slots=True)
class Contact:
    """Quem está conversando, do ponto de vista do agente."""

    channel: Channel              # TELEGRAM
    channel_user_id: str          # id do usuário no canal (chat_id do Telegram)
    display_name: str | None      # nome exibido, quando o canal informa
    phone: str                    # telefone canônico usado na sessão do AgendaBot


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
    tool_calls_made: int          # observabilidade; não vai para o usuário


@dataclass(frozen=True, slots=True)
class BookingSession:
    """A sessão autenticada do cliente no AgendaBot."""

    token: str
    phone: str                    # telefone canônico que originou a sessão; chave do cache
    client_id: uuid.UUID
    client_name: str
    expires_at: datetime
    is_new_client: bool

    def is_valid_at(self, moment: datetime) -> bool:
        """Diz se a sessão ainda vale no instante dado."""


@dataclass(frozen=True, slots=True)
class ConversationRef:
    """Identifica a thread de conversa no checkpointer."""

    channel: Channel
    channel_user_id: str

    @property
    def thread_id(self) -> str:
        """A chave estável da thread: `telegram:123456`."""
```

## Enums

```python
class Channel(StrEnum):
    TELEGRAM = "telegram"
```

Um único valor hoje, mas o campo existe desde já: é ele que impede que a chave de
thread do Telegram colida com a do WhatsApp quando ele entrar.

## Erros

`app/modules/agent/domain/exceptions.py`

```python
class AgentError(Exception):
    """Base de todo erro esperado do agente."""

    user_message: str = "Tive um problema aqui. Pode tentar de novo em instantes?"


class BookingSessionError(AgentError):
    """Não foi possível abrir a sessão do cliente no AgendaBot."""


class ClientBlockedError(BookingSessionError):
    """O cliente existe mas está inativo no estabelecimento."""

    user_message = "Não consigo te atender por aqui. Fale direto com o estabelecimento."


class AgentUnavailableError(AgentError):
    """O LLM falhou ou estourou o tempo."""


class ConversationStateError(AgentError):
    """Não foi possível ler ou gravar o estado da conversa."""


class DeliveryError(AgentError):
    """A resposta não pôde ser entregue ao canal."""


class InvalidPhoneError(AgentError):
    """O telefone do contato não pôde ser determinado."""
```

Cada erro carrega o `user_message` — a frase que o canal mostra ao cliente. Isso
mantém a decisão "o que o cliente lê quando dá errado" no domínio, e não espalhada
por `try/except` nos adapters.

## O que **não** existe aqui

Não há entidades `Service`, `Slot` ou `Scheduling`. Esses conceitos pertencem ao
AgendaBot; o agente os enxerga apenas como JSON dentro do resultado de uma tool, e
quem os interpreta é o LLM. Duplicar esse modelo aqui criaria duas fontes de verdade
para regras que o agente não é dono.
