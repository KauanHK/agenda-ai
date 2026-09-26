# 06 — Cliente da Bot API no módulo `channels`

**Repositório:** agenda2 · **Depende de:** 02, 05 · **Estimativa:** ~110 linhas

## Objetivo

Ter um só cliente para as chamadas de administração do bot (`getMe`, `setWebhook`,
`deleteWebhook`, `getWebhookInfo`). O token é passado **por chamada**, porque o SaaS vai
falar com vários bots. O ponto de partida é o `TelegramWebhookRegistry` do agente, que
hoje está preso a um token e a um segredo fixos.

## Contexto

O agente já tem, em `adapters/telegram/webhook_registry.py`, o `setWebhook` e o
`getWebhookInfo`, com tradução de erro e mascaramento do segredo. Esta PR **move e
generaliza** esse código para o dono novo, o módulo `channels`, que conecta os bots. Não
cria uma segunda implementação.

## Mudanças

### Módulo `channels`

- **`domain/entities.py`:** `BotIdentity(id: int, username: str)`.
- **`domain/exceptions.py`:**
  - `InvalidBotTokenError`: a Bot API respondeu `401` ou `404` (token revogado,
    inexistente ou malformado).
  - `TelegramApiError`: falha de transporte, timeout, `429`, `5xx` ou `ok: false` por
    outro motivo.
- **`application/ports/telegram_bot_api.py`** → `TelegramBotApiProtocol`:
  - `get_me(bot_token) -> BotIdentity`
  - `set_webhook(bot_token, *, url, secret_token, drop_pending_updates=False) -> None`
  - `delete_webhook(bot_token, *, drop_pending_updates) -> None`
  - `get_webhook_info(bot_token) -> dict[str, Any]`: existe só para a rota
    administrativa do agente, que sai na spec 11. Se não sobrar ninguém usando, sai junto.
- **`adapters/telegram/bot_api.py`** → `TelegramBotApi(client: httpx.AsyncClient)`:
  - O client tem `base_url` = raiz da Bot API, **sem** token. Uma factory
    `build_bot_api_client()` define os timeouts (connect curto, read curto: a Bot API
    responde rápido ou não responde).
  - Cada chamada monta `/bot{token}/{método}`.
  - `set_webhook` manda `allowed_updates=["message"]`, que é o que o parser do agente
    entende, e o `secret_token`.
  - **Nada sensível sai daqui:**
    - erros levantados com `from None`, porque o `__cause__` do httpx carrega a URL com o
      token;
    - `description` do Telegram com o token e o segredo trocados por `***`;
    - `get_webhook_info` devolve a `url` com o segredo mascarado.

### Agente

- `adapters/telegram/webhook_registry.py` sai.
- O container monta um `TelegramBotApi`. A rota `/admin/telegram/webhook` e os scripts
  `set_webhook` e `delete_webhook` passam a chamá-lo com o token e o segredo fixos das
  settings. A montagem da URL (`base_url + /webhook/telegram/{segredo}`) vai para o
  container.
- `InvalidBotTokenError` e `TelegramApiError` viram `WebhookRegistrationError` na borda do
  agente. Para quem chama a rota administrativa, nada muda (continua `502`).

## Testes

Os testes do registry são movidos e adaptados, usando `respx` ou `httpx.MockTransport`:

- `get_me` com `200 ok:true` devolve `BotIdentity`; com `401` levanta
  `InvalidBotTokenError`.
- `set_webhook` manda url, `secret_token`, `allowed_updates` e `drop_pending_updates`
  no corpo, para `/bot{token}/setWebhook`.
- `delete_webhook` repassa `drop_pending_updates`.
- `5xx`, `429`, timeout e `ok:false` levantam `TelegramApiError`.
- **Nenhum** erro levantado tem o token ou o segredo em `str(exc)`, e `__cause__` é
  `None`.
- `get_webhook_info` mascara o segredo na `url`.
- Rotas administrativas do agente: os testes atuais continuam verdes, com o fake do
  cliente novo.

## Critérios de aceite

- `rg WebhookRegistry` não encontra nada.
- Em produção, `scripts.agent.set_webhook` continua funcionando. Rodar uma vez com a
  mesma URL não muda nada.

## Deploy

Deploy normal, sem mudança de env.
