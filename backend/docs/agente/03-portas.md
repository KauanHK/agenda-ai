# 03 — Portas

`app/modules/agent/application/ports/`. Todas são `typing.Protocol` — sem herança, sem ABC: o
adapter satisfaz o contrato por estrutura, e o teste substitui por um fake trivial.

Regra: **uma porta por motivo de mudança**. Emitir sessão e cachear sessão são portas
separadas porque uma muda quando a API do AgendaBot muda e a outra quando o Redis muda.

## `PhoneResolverProtocol`

```python
class PhoneResolverProtocol(Protocol):
    def resolve(self, channel: Channel, channel_user_id: str) -> str:
        """Devolve o telefone canônico do contato, no formato E.164 sem '+'."""
```

Síncrono e sem I/O na fase 1 (derivação determinística). A porta existe para que a
troca por "perguntar o número na conversa" ou por `request_contact` seja uma
substituição de adapter — inclusive uma assíncrona, quando chegar a hora de trocar a
assinatura por `async def`.

## `BookingSessionIssuerProtocol`

```python
class BookingSessionIssuerProtocol(Protocol):
    async def issue(
        self, establishment_id: uuid.UUID, phone: str, name: str | None
    ) -> BookingSession:
        """
        Troca o telefone por uma sessão autenticada no estabelecimento.

        Raises:
            ClientBlockedError: Se o cliente está inativo no estabelecimento.
            BookingSessionError: Em qualquer outra falha de emissão.
        """
```

## `SessionTokenCacheProtocol`

```python
class SessionTokenCacheProtocol(Protocol):
    async def get(self, establishment_id: uuid.UUID, phone: str) -> BookingSession | None:
        """Devolve a sessão cacheada do telefone no estabelecimento, ou `None`."""

    async def put(self, session: BookingSession) -> None:
        """Guarda a sessão até pouco antes de ela expirar."""
```

## `BookingToolProviderProtocol`

```python
class BookingToolProviderProtocol(Protocol):
    async def tools_for(self, session_token: str) -> Sequence[Any]:
        """
        Carrega as tools do MCP server autenticadas com o token da sessão.

        O tipo do elemento é opaco para a aplicação de propósito: quem sabe o que é
        uma tool é o runner do agente, que a recebe e repassa. A aplicação apenas
        garante que o token certo chegou ao provider certo.
        """
```

> `Sequence[Any]` é uma concessão consciente. A alternativa — modelar `Tool` no domínio
> e converter para `BaseTool` do LangChain — só adicionaria uma camada de tradução sem
> nenhum ponto de decisão nossa no meio.

## `AgentRunnerProtocol`

```python
class AgentRunnerProtocol(Protocol):
    async def run(
        self,
        *,
        conversation: ConversationRef,
        user_text: str,
        tools: Sequence[Any],
        context: AgentContext,
    ) -> AgentAnswer:
        """
        Roda um turno do agente sobre o histórico da conversa.

        Raises:
            AgentUnavailableError: Se o modelo falhar ou estourar o tempo.
            ConversationStateError: Se o histórico não puder ser lido ou gravado.
        """
```

`AgentContext` é um dataclass do domínio com o que o system prompt precisa e que não
vem do histórico: nome do cliente, data/hora atual no fuso do estabelecimento, e se é
um cliente novo.

## `OutboundMessengerProtocol`

```python
class OutboundMessengerProtocol(Protocol):
    async def send_text(self, conversation: ConversationRef, text: str) -> None:
        """Entrega um texto na conversa. Levanta `DeliveryError` se não conseguir."""

    async def signal_typing(self, conversation: ConversationRef) -> None:
        """Sinaliza ao canal que a resposta está sendo produzida. Falha em silêncio."""
```

Recebe `ConversationRef`, e não `Contact`: é a conversa (canal + estabelecimento +
usuário) que diz por qual bot responder.

`signal_typing` não levanta: um indicador de digitação que não apareceu não é motivo
para abortar a resposta.
