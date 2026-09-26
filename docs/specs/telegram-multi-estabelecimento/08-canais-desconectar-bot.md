# 08 — Desconectar o bot

**Repositório:** agenda2 · **Depende de:** 07 · **Estimativa:** ~50 linhas

## Objetivo

Permitir remover o bot de um estabelecimento. O Telegram para de entregar no agente e o
token sai do banco.

## Contrato HTTP

**`DELETE /api/establishments/{establishment_id}/channels/telegram`**

| Situação | Status |
|---|---|
| Desconectado | 204 |
| Nenhum bot conectado | 404 |
| O Telegram não respondeu ou deu erro | 502, e **o bot continua conectado** |
| Sem permissão | 403 (mesma regra de conectar: `global_admin` ou `establishment_admin`) |

## Fluxo de `TelegramBotDisconnector.disconnect(actor, establishment_id)`

1. `assert_can_manage`.
2. No UoW, `bot = telegram_bots.get_by_establishment(...)`. Se não houver, `NotFoundError`.
3. `bot_api.delete_webhook(bot.bot_token, drop_pending_updates=True)`. As mensagens
   pendentes não interessam mais.
   - `InvalidBotTokenError`: o token foi revogado no @BotFather, então não há webhook
     ativo para remover. **Segue** para o passo 4.
   - `TelegramApiError`: **aborta** sem apagar a linha. Se apagasse, o webhook
     continuaria ativo e o Telegram ficaria reenviando mensagens para um agente que
     responde `404`, sem nada no painel indicando o problema. Com o `502`, o admin tenta
     de novo.
4. `telegram_bots.delete(establishment_id)` e commit.

## Mudanças

- `application/use_cases/disconnect_telegram.py`.
- Rota `DELETE` no `router.py` do módulo, com a dependência correspondente.

## Testes

- Sucesso: chama `delete_webhook` com o token do bot e `drop_pending_updates=True`, e
  apaga a linha.
- Token revogado (`InvalidBotTokenError`): apaga a linha mesmo assim.
- `TelegramApiError`: não apaga e responde 502.
- Sem bot: 404, sem chamar o Telegram.
- Permissões: `member` → 403; `global_admin` → ok.

## Critérios de aceite

- Localmente: depois do `DELETE`, o `getWebhookInfo` do bot de teste mostra a `url`
  vazia e o `GET` do painel volta `connected: false`.

## Deploy

Deploy normal.
