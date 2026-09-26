# 10 — Testes

`pytest` + `pytest-asyncio` em modo `auto`. Espelha a estrutura de `src/`.

## Por camada

| Camada | Como | Sem |
| --- | --- | --- |
| `domain` | teste unitário direto | mocks |
| `application` | use case com fakes das portas | rede, Redis, LLM |
| `infrastructure` | adapter contra dublê do serviço | serviço real |
| `interfaces` | `TestClient` do FastAPI com container fake | tudo externo |

Cada porta ganha um fake em `tests/modules/agent/fakes/` — classes de ~10 linhas, não `MagicMock`. Um
fake que não satisfaz o `Protocol` é pego pelo `mypy`; um `MagicMock` aceita qualquer
chamada errada em silêncio.

## Casos que precisam existir

### Domínio
- `BookingSession.is_valid_at` na borda exata da expiração.
- `ConversationRef.thread_id` estável e sem colisão entre canais.

### `HandleIncomingMessage`
- Caminho feliz: uma resposta enviada, uma vez.
- `BookingSessionError` → cliente recebe o `user_message`, e o agente **não** roda.
- `ClientBlockedError` → mensagem específica de cliente inativo.
- Exceção inesperada no runner → frase padrão, sem vazar detalhe, `logger.exception`.
- Falha em `signal_typing` não impede a resposta.

### `BookingSessionProvider`
- Cache hit → não chama o issuer.
- Sessão expirando dentro da margem → reemite.
- Cache indisponível → reemite e segue.

### `session_issuer` (com UoW falso do booking)
- Sucesso → `BookingSession` com `expires_at` calculado pelo relógio injetado.
- Cliente inativo → `ClientBlockedError`; telefone inválido → `InvalidPhoneError`.
- Estabelecimento indisponível, erro de banco ou de rede → `BookingSessionError`.
- `ConflictError` → uma nova tentativa; repetido → `BookingSessionError`.

### Grafo
- `should_continue` com e sem `tool_calls`.
- `call_tools` executa em paralelo, casa `tool_call_id`, e converte exceção de tool em
  `ToolMessage` de erro.
- Tool inexistente não derruba o turno.
- `trim_history` nunca separa `AIMessage` com `tool_calls` dos seus `ToolMessage`.
- Estouro de `recursion_limit` → `AgentUnavailableError`.
- Resposta final vazia → texto de fallback.

Nesses testes o LLM é um `FakeChatModel` com respostas roteirizadas — inclusive uma que
pede tool call e outra que responde texto. Nenhum teste automático chama a API do
provider.

### Telegram
- `parse_update` devolve `None` para: update sem `message`, sem `text`,
  `edited_message`, mensagem de bot, chat de grupo.
- Webhook: id que não é UUID, estabelecimento sem bot, header ausente, errado ou com o
  segredo de **outro** bot → 404; diretório fora → 503; nenhum dos dois agenda
  processamento.
- `TelegramMessenger`: cada conversa sai pelo bot do seu estabelecimento; bot ausente →
  `DeliveryError`; nenhum erro carrega o token.
- De ponta a ponta no handler: o mesmo `chat_id` em dois bots gera threads e sessões
  separadas, e cada resposta sai pelo bot certo.
- Webhook responde 200 antes de o processamento terminar.
- `split_for_telegram` respeita 4096 e não corta palavra no meio.
- `to_telegram_text` remove `**` e `##` e colapsa linhas em branco.

### Identidade
- `SyntheticPhoneResolver` é determinístico e usa o prefixo configurado.

### Arquitetura
- `tests/modules/agent/test_dependencies.py` valida a tabela de imports permitidos do doc 01.

## Teste de integração manual

Um `scripts/agent/smoke_mcp.py` que emite uma sessão de verdade, conecta no MCP e lista as
tools — roda à mão, contra o ambiente real, e não faz parte da suíte. É o que responde
"o contrato mudou?" sem precisar de mock.

## Qualidade

`ruff check`, `ruff format --check` e `mypy --strict` sobre `src/`, no CI junto com a
suíte.
