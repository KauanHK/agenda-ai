# 07 — Conectar o bot e consultar o status

**Repositório:** agenda2 · **Depende de:** 06 · **Estimativa:** ~160 linhas

## Objetivo

Permitir que o admin do estabelecimento (ou o admin global) conecte o bot do Telegram
colando o token gerado no @BotFather. Conectar faz três coisas: valida o token, registra
o webhook apontando para o agente e guarda o bot. Também é possível consultar o status.

## Contrato HTTP

Montado em `build_establishment_router()` com o prefixo `/channels/telegram` e a tag
`Channels`.

**`GET /api/establishments/{establishment_id}/channels/telegram`** responde `200` com
`TelegramChannelRead`:

```json
{ "connected": true, "bot_id": 123456789, "bot_username": "barbearia_x_bot", "connected_at": "2026-09-25T20:00:00Z" }
```

Sem bot, a resposta é `{"connected": false, "bot_id": null, "bot_username": null,
"connected_at": null}`. Assim a tela não precisa tratar `404` como estado normal.
**Nunca** devolve token nem segredo.

**`PUT /api/establishments/{establishment_id}/channels/telegram`**

- Corpo: `{"bot_token": "123456789:AA..."}`.
- Resposta: `200` com `TelegramChannelRead`.
- Erros:

| Situação | Status | Mensagem |
|---|---|---|
| Token fora do formato `^\d+:[A-Za-z0-9_-]{30,}$` (checado no schema, antes de chamar o Telegram) | 422 | validação do Pydantic |
| O Telegram recusou o token | 422 | "Token do bot inválido. Confira com o @BotFather." |
| O bot já está conectado a **outro** estabelecimento | 409 | "Este bot já está conectado a outro estabelecimento." |
| Estabelecimento inexistente | 404 | — |
| O Telegram não respondeu ou deu erro | 502 | "Não foi possível falar com o Telegram. Tente novamente." |
| Sem permissão | 403 | — |

O `502` pede um `ExternalServiceError(AppError)` novo em `app/core/exceptions.py`
(`status_code=502`, `code="external_service_error"`), que hoje não existe.

## Autorização (`channels/application/authz.py`)

- **Ler:** `actor.is_member_of(establishment_id)`. O `global_admin` já está incluído.
- **Conectar e desconectar:** `global_admin`, ou `ESTABLISHMENT_ADMIN` naquele
  estabelecimento.

É diferente de `operating_hours`, que recusa `global_admin`, e de propósito: o admin
global faz o onboarding. Um comentário no `authz.py` registra isso.

## Fluxo de `TelegramBotConnector.connect(actor, establishment_id, bot_token)`

1. `assert_can_manage`.
2. `identity = bot_api.get_me(bot_token)`. Se o Telegram recusar, levanta
   `InvalidBotTokenError`.
3. Abre o UoW:
   1. O estabelecimento precisa existir (`uow.establishments`), senão `NotFoundError`.
      Estabelecimento inativo **pode** conectar; o agente ignora estabelecimentos
      inativos (spec 10).
   2. `owner = telegram_bots.get_by_bot_id(identity.id)`. Se existir e for de outro
      estabelecimento, `ConflictError`.
   3. `current = telegram_bots.get_by_establishment(establishment_id)`.
   4. `secret = secrets.token_urlsafe(32)`: segredo novo a cada conexão. Reconectar
      também gira o segredo, e o agente lê do banco sem cache (spec 10), então a troca
      vale na hora.
   5. `bot_api.set_webhook(bot_token, url=f"{TELEGRAM_WEBHOOK_BASE_URL}/webhook/telegram/{establishment_id}", secret_token=secret)`.
      Sem `drop_pending_updates`: numa troca de host ou de bot, as mensagens pendentes
      seguem para a URL nova.
   6. Se `current` era **outro** bot, `bot_api.delete_webhook(current.bot_token)` em
      modo best-effort: loga um `warning` em falha e não aborta. O bot antigo deixa de
      bater no agente.
   7. `telegram_bots.save(...)` e commit.

As chamadas ao Telegram ficam dentro do UoW: é ação administrativa e rara, e segurar a
conexão durante esse tempo é aceitável. Se o `set_webhook` falhar, nada é gravado. Se o
commit falhar depois do `set_webhook`, o webhook aponta para o agente sem bot gravado; o
agente responde `404` (spec 11) e o admin repete a operação. Isso fica documentado na
docstring.

Dois estabelecimentos conectando o mesmo bot ao mesmo tempo: a `UNIQUE(bot_id)` barra o
segundo commit, e o `IntegrityError` vira `ConflictError`.

## Mudanças

- **`app/core/settings.py`:** `TELEGRAM_WEBHOOK_BASE_URL`, a base HTTPS pública onde o
  nginx expõe `/webhook/`. Em produção é o próprio domínio do SaaS; em dev é o túnel.
  - Um validador exige `https://` e remove a `/` final.
  - É uma variável própria (e não o `FRONTEND_URL`) porque em dev os dois são diferentes.
- **`application/use_cases/`:** `connect_telegram.py` (`TelegramBotConnector`) e
  `read_telegram.py` (`TelegramBotReader.get(actor, establishment_id) -> TelegramBot | None`).
- **`adapters/http/`:** `schemas.py` (`TelegramChannelConnect`, `TelegramChannelRead`),
  `dependencies.py` e `router.py`.
  - O `TelegramBotApi` é montado por requisição com `async with build_bot_api_client()`.
    Conectar é raro, e um client global na API não se paga.
- **`app/api/router.py`:** inclui o router.
- **`.env.example`:** `TELEGRAM_WEBHOOK_BASE_URL`.

## Testes

- **`TelegramBotConnector`**, com UoW e `TelegramBotApi` falsos:
  - sucesso: grava o bot com `bot_id` e `username` do `getMe` e registra a URL com o
    `establishment_id`;
  - reconectar o mesmo bot: o segredo muda e não chama `delete_webhook`;
  - trocar de bot: chama `delete_webhook` com o token **antigo**, e uma falha nele não
    impede a troca;
  - bot de outro estabelecimento: `ConflictError`, sem `set_webhook` e sem gravar;
  - token recusado: `InvalidBotTokenError`, sem gravar;
  - `set_webhook` falha: nada gravado;
  - permissões: `member` → 403; `establishment_admin` de **outro** estabelecimento → 403;
    `global_admin` → ok.
- **Router** (padrão de app de teste com overrides):
  - status e corpo de cada linha da tabela de erros;
  - `GET` sem bot → `connected: false`;
  - **nenhuma resposta contém o token**.

## Critérios de aceite

- No ambiente local com túnel: `PUT` com um bot de teste deixa o `getWebhookInfo`
  apontando para `{túnel}/webhook/telegram/{establishment_id}`.

## Deploy

1. Colocar `TELEGRAM_WEBHOOK_BASE_URL=https://agenda.escaleia.cloud` na VPS antes do merge.
2. **Não conectar o bot de produção até o deploy da spec 11**: a rota nova ainda não
   existe e o bot pararia de responder.
