# 04 — Casos de uso

`src/application/use_cases/`. Uma classe por caso de uso, um método público `execute`.
Todas as dependências entram pelo `__init__` como portas.

## `HandleIncomingMessage`

O único caso de uso do caminho principal. Recebe uma `IncomingMessage` já parseada e
devolve nada — o efeito é a resposta entregue ao canal.

```python
class HandleIncomingMessage:
    def __init__(
        self,
        session_provider: BookingSessionProvider,   # use case, não porta
        tool_provider: BookingToolProviderProtocol,
        agent: AgentRunnerProtocol,
        messenger: OutboundMessengerProtocol,
    ) -> None: ...

    async def execute(self, message: IncomingMessage) -> None:
        """
        Atende uma mensagem do cliente de ponta a ponta.

        Falhas esperadas (`AgentError`) não sobem: viram uma resposta em linguagem
        natural para o cliente, usando o `user_message` do erro. Quem chama (o webhook)
        nunca precisa decidir o que o cliente lê.
        """
```

Sequência:

1. `signal_typing` no canal.
2. `session_provider.for_contact(message.contact)` → `BookingSession`.
3. `tool_provider.tools_for(session.token)` → tools.
4. `agent.run(...)` → `AgentAnswer`.
5. `messenger.send_text(...)`.

O passo 1 não bloqueia o resto: se falhar, é ignorado.

### Tratamento de erro

```python
try:
    answer_text = await self._produce_answer(message)
except AgentError as error:
    answer_text = error.user_message
    logger.warning("Turno falhou para %s: %s", ref, error)
await self._messenger.send_text(message.contact, answer_text)
```

`_produce_answer` é privado e concentra os passos 2–4. `execute` fica com uma única
responsabilidade: garantir que **sempre** sai uma resposta.

Um erro inesperado (não `AgentError`) é logado com `logger.exception` e responde com a
frase padrão de `AgentError` — o cliente nunca vê stacktrace nem detalhe interno.

## `BookingSessionProvider`

Caso de uso, não adapter: a política de "usa o cache, senão emite, e guarda" é decisão
de aplicação.

```python
class BookingSessionProvider:
    def __init__(
        self,
        phone_resolver: PhoneResolverProtocol,
        issuer: BookingSessionIssuerProtocol,
        cache: SessionTokenCacheProtocol,
        clock: Callable[[], datetime],
        refresh_margin_seconds: int,          # SESSION_REFRESH_MARGIN_SECONDS
    ) -> None: ...

    async def for_contact(self, contact: Contact) -> BookingSession:
        """Devolve uma sessão válida para o contato, reaproveitando o cache."""
```

- O telefone vem do `phone_resolver` (o `Contact` já o carrega; quem monta o `Contact`
  é o parser do canal, que usa a mesma porta).
- Cache miss ou sessão expirando em menos de `SESSION_REFRESH_MARGIN_SECONDS` → emite
  de novo.
- `clock` é injetado para que o teste controle o tempo sem `freezegun`.

## `ResetConversation`

```python
class ResetConversation:
    async def execute(self, conversation: ConversationRef) -> None:
        """Descarta o histórico da conversa, começando do zero."""
```

Atende o comando `/reset` (e `/start`) do Telegram. Apaga os checkpoints da thread no
Redis; não apaga o cache de token nem nada no AgendaBot.

## O que os use cases **não** fazem

- Não formatam Markdown (é do adapter do Telegram).
- Não montam prompt (é do runner).
- Não leem `os.environ` (recebem valores prontos).
- Não sabem que existe LangGraph, Redis, `httpx` ou MCP.
