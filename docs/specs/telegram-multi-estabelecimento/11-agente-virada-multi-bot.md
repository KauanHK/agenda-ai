# 11 — Virada: webhook e envio por estabelecimento

**Repositório:** agenda2 · **Depende de:** 07 (em produção), 10 · **Estimativa:** ~120 linhas

## Objetivo

O agente passa a atender qualquer estabelecimento que tenha um bot conectado. O
`establishment_id` na URL do webhook escolhe o bot; o segredo daquele bot autentica o
update; a resposta sai pelo mesmo bot. A configuração fixa e a administração do webhook
pelo agente são removidas.

## Contrato do webhook

**`POST /webhook/telegram/{establishment_id}`**, chamada pelo Telegram. A URL é
registrada pela spec 07.

| Situação | Resposta |
|---|---|
| `establishment_id` não é UUID | 404 |
| O diretório devolve `None` (sem bot, estabelecimento inativo ou inexistente) | 404 |
| Header `X-Telegram-Bot-Api-Secret-Token` ausente ou diferente do segredo do bot (`hmac.compare_digest`) | 404 |
| `ChannelLookupError` (banco fora) | 503, para o Telegram reenviar |
| Ok | 200 `{"ok": true}` na hora; o turno roda em background, como hoje |

- **Sempre `404`, nunca `401`/`403`:** o que já é regra hoje. Um `403` confirmaria que a
  rota existe para aquele id.
- **O header passa a ser obrigatório.** Hoje ele é opcional porque o segredo também vai
  no caminho. Agora o caminho é só um UUID, que não é segredo; o header é a
  autenticação.
- **O path param é recebido como `str` e convertido à mão.** Um `uuid.UUID` no path faria
  o FastAPI responder `422`.

## Mudanças

- **`adapters/http/routes/telegram.py`:** a rota acima. Resolve o canal pelo diretório
  (spec 10), valida o header e agenda `handle_update(channel.establishment, payload)`.
- **`TelegramWebhookHandler.handle_update(establishment, payload)`:** repassa o
  estabelecimento ao `parse_update`. Deixa de existir o `partial` com o estabelecimento
  fixo da spec 09.
- **`TelegramMessenger(client, directory)`:**
  - O `client` passa a ter `base_url` = raiz da Bot API, **sem token**.
  - `send_text` e `signal_typing` resolvem o canal por `conversation.establishment_id` e
    chamam `/bot{token}/sendMessage` ou `/sendChatAction`.
  - Canal `None` na hora de responder (desconectado no meio do turno) → `DeliveryError`,
    no `send_text`. O `signal_typing` continua engolindo a falha.
  - Mantém o `from None` nos erros. Com a spec 01, o `httpx` não loga a URL.
- **Container:**
  - Monta `DbTelegramChannelDirectory` e o messenger multi-bot.
  - O `Container` passa a ter `handle_update`, `channels` (o diretório, para a rota) e
    `check_readiness`.
  - Saem `webhook_secret`, `admin_token`, `register_webhook` e `get_webhook_info`.
- **Removidos:**
  - rota `/admin/telegram/webhook` (`routes/admin.py`) e os testes;
  - scripts `scripts/agent/set_webhook.py` e `delete_webhook.py`;
  - `TelegramBotApi.get_webhook_info` e o método correspondente no protocolo, se não
    sobrar ninguém usando (spec 06);
  - settings `AGENT_AGENDABOT__ESTABLISHMENT_ID`, `AGENT_AGENDABOT__ESTABLISHMENT_TIMEZONE`,
    `AGENT_TELEGRAM__BOT_TOKEN`, `AGENT_TELEGRAM__WEBHOOK_SECRET` e
    `AGENT_TELEGRAM__ADMIN_TOKEN`, com as entradas no `.env.example`.
- **`scripts/agent/repl.py` e `smoke_mcp.py`** recebem `--establishment-id` e pegam o fuso
  pelo diretório.
- **Documentação** em `backend/docs/agente/`: atualizar canal, configuração e roadmap. O
  item "`establishment_id` por canal" sai do "Depois".

## Testes

- **Rota:**
  - cada linha da tabela do contrato;
  - o header certo de **outro** estabelecimento → 404;
  - `404` e `503` não disparam processamento em background.
- **`TelegramMessenger`** (com `MockTransport`):
  - conversas de dois estabelecimentos saem por `/bot{tokenA}/…` e `/bot{tokenB}/…`;
  - canal ausente → `DeliveryError`;
  - nenhum erro carrega o token.
- **De ponta a ponta no handler**, com diretório falso de dois estabelecimentos: o mesmo
  `chat_id` nos dois bots gera threads diferentes, sessões emitidas para o
  estabelecimento certo e respostas pelo bot certo.

## Passo a passo da virada (checklist da PR)

Pré-requisito: specs 05–08 em produção, com `CHANNEL_SECRETS_KEY` e
`TELEGRAM_WEBHOOK_BASE_URL` configuradas.

1. Merge e deploy. A partir daqui, o webhook antigo (`/webhook/telegram/{segredo-antigo}`)
   responde `404`, e o Telegram guarda os updates e tenta de novo.
2. **Logo em seguida**, como `global_admin`, conectar o bot atual ao estabelecimento dele:
   `PUT /api/establishments/01a04f5b-0e84-7530-be67-63f08e7b2269/channels/telegram` com o
   token atual. O `setWebhook` aponta para a URL nova e os pendentes são entregues. O
   painel (spec 12) ainda não está no ar; usar o Swagger (`/api/docs`) ou `curl`.
3. Mandar uma mensagem e conferir a resposta.
4. Remover da VPS as cinco variáveis que saíram.

**A janela entre os passos 1 e 2 precisa ser de minutos:** a Bot API desiste de reenviar
depois de "um número razoável de tentativas".

**Rollback:** reverter o deploy e rodar o `set_webhook` da versão anterior com o segredo
antigo, que ainda está no `.env` até o passo 4.

## Critérios de aceite

- Dois bots de teste conectados a dois estabelecimentos no ambiente local: o mesmo
  usuário do Telegram fala com os dois, e cada um agenda no próprio estabelecimento, com
  históricos separados.
- `rg "ESTABLISHMENT_ID|BOT_TOKEN|WEBHOOK_SECRET|ADMIN_TOKEN" backend/app/modules/agent`
  não encontra nada.
