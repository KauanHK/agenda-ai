# Bots do Telegram por estabelecimento

Planejamento de 2026-09-25. Cada arquivo numerado é uma spec e vira **uma PR**, com no
máximo ~200 linhas de regra de negócio (testes, docs, migrations e código só movido
não contam).

## Onde estamos

- **SaaS** (`backend/`): já atende vários estabelecimentos. O MCP tira `establishment_id`
  e `client_id` do token de sessão, e `POST /api/agent/{establishment_id}/sessions`
  recebe o estabelecimento pela URL.
- **Agente** (repositório `agente-agenda`, container separado na mesma VPS): um único bot,
  com `AGENDABOT__ESTABLISHMENT_ID`, `_TIMEZONE`, `TELEGRAM__BOT_TOKEN` e
  `TELEGRAM__WEBHOOK_SECRET` fixos no env.

Problemas que aparecem assim que existir um segundo bot. No Telegram, o `chat_id` de uma
conversa privada é o id do usuário, igual em todos os bots:

1. O cache de sessão usa a chave `sha256(phone)`, e o telefone sintético deriva do
   `chat_id`. O mesmo usuário falando com o bot B reaproveitaria o token do
   estabelecimento A e **agendaria no estabelecimento errado**.
2. A conversa é guardada como `telegram:{chat_id}`: os históricos dos dois
   estabelecimentos se misturariam.
3. **Já acontece hoje:** o `httpx` registra no log, em INFO, a URL que carrega o token
   do bot (`https://api.telegram.org/bot<token>/sendMessage`). Reproduzido com o
   `configure_logging` do agente.

## Decisões

| Decisão | Escolha | Por quê |
|---|---|---|
| Onde fica o agente | **Neste repositório, antes desta entrega**, como outro processo da mesma imagem (padrão do `app.main_mcp`) | A questão central aqui é quem guarda os dados: token, fuso e status do estabelecimento ficam no Postgres. Em outro repositório, seria preciso um endpoint que devolve segredo em claro, um cache com TTL do outro lado e contratos duplicados sem teste que pegue divergência. A stack é a mesma (Python 3.14, FastAPI, uv, Redis, httpx), assim como a VPS. |
| Quem guarda o bot | O SaaS (tabela `telegram_bots`) | Fica junto do resto do cadastro e o painel já administra estabelecimentos. |
| Quem registra o webhook | O SaaS, ao conectar o bot pelo painel | O painel dá retorno imediato (token inválido, bot já em uso) e o agente não precisa de rota administrativa. |
| Roteamento de mensagens | `establishment_id` na URL do webhook | Um bot por estabelecimento, então a URL identifica o bot. A autenticação é o header `X-Telegram-Bot-Api-Secret-Token`, que passa a ser obrigatório; o UUID não é segredo. |
| Quem conecta e desconecta | `establishment_admin` do estabelecimento e `global_admin`; qualquer membro vê o status | O `global_admin` cobre o onboarding. É diferente de `operating_hours`, que recusa `global_admin`; aqui a diferença é intencional. |
| Painel | Entra nesta entrega (spec 12) | — |

A fronteira "MCP + token de sessão" continua existindo mesmo com tudo no mesmo
repositório. É ela que impede o LLM de agir fora do escopo do cliente, e não mudou.

## Arquitetura final

```
Telegram ──POST /webhook/telegram/{establishment_id}──▶ nginx ──▶ agent (app.main_agent, :8002)
            header X-Telegram-Bot-Api-Secret-Token                  │
                                                                     ├─ telegram_bots + establishments (Postgres, lido direto)
                                                                     ├─ CustomerSessionIssuer (no próprio processo) ─▶ token de sessão
                                                                     ├─ MCP (http://mcp:8001/mcp, Bearer token de sessão)
                                                                     ├─ agent-redis (histórico e cache, chaveados por estabelecimento)
                                                                     └─ Bot API: sendMessage com o token do bot daquele estabelecimento

Painel ──PUT/GET/DELETE /api/establishments/{id}/channels/telegram──▶ api
                                                      getMe + setWebhook/deleteWebhook na Bot API
```

## Invariantes

1. No máximo um bot por estabelecimento (PK `establishment_id`).
2. Um bot pertence a no máximo um estabelecimento (`bot_id` único). Sem isso, o segundo
   `setWebhook` tomaria o bot do primeiro sem aviso.
3. O token e o segredo do webhook ficam cifrados no banco, nunca voltam para o painel e
   nunca aparecem em log ou mensagem de erro.
4. O agente só aceita um update que traga o segredo do bot daquele estabelecimento.
5. Todo estado do agente (histórico e cache de sessão) é chaveado por estabelecimento.
6. O LLM continua sem ver `establishment_id` e `client_id`: tudo vem do token do MCP.

## Specs

| # | Spec | Onde | Depende de | Linhas* |
|---|---|---|---|---|
| 01 | [Não logar a URL com o token do bot](01-agente-log-sem-token.md) | `agente-agenda` | — | ~5 |
| 02 | [Mover o agente para o backend](02-migracao-mover-codigo.md) | agenda2 | 01 | ~30 (resto é movido) |
| 03 | [Subir o agente no stack do agenda2](03-migracao-subir-no-stack.md) | agenda2 | 02 | ~0 (infra) |
| 04 | [Sessão emitida no próprio processo](04-migracao-sessao-no-processo.md) | agenda2 | 03 | ~70 |
| 05 | [Guardar o bot cifrado por estabelecimento](05-canais-armazenamento.md) | agenda2 | — | ~140 |
| 06 | [Cliente da Bot API no módulo `channels`](06-canais-cliente-bot-api.md) | agenda2 | 02, 05 | ~110 |
| 07 | [Conectar o bot e consultar o status](07-canais-conectar-bot.md) | agenda2 | 06 | ~160 |
| 08 | [Desconectar o bot](08-canais-desconectar-bot.md) | agenda2 | 07 | ~50 |
| 09 | [Estado do agente por estabelecimento](09-agente-estado-por-estabelecimento.md) | agenda2 | 04 | ~90 |
| 10 | [Diretório de canais do agente](10-agente-diretorio-de-canais.md) | agenda2 | 05, 09 | ~60 |
| 11 | [Virada: webhook e envio por estabelecimento](11-agente-virada-multi-bot.md) | agenda2 | 07, 10 | ~120 |
| 12 | [Card do Telegram no painel](12-painel-card-telegram.md) | agenda2 | 08, 11 no ar | ~150 (TSX) |

\* Estimativa de regra de negócio, sem testes, docs, migrations e código movido.

```
01 ─▶ 02 ─▶ 03 ─▶ 04 ─▶ 09 ─┐
       │                    ├─▶ 10 ─▶ 11 ─▶ 12
05 ────┴─▶ 06 ─▶ 07 ─▶ 08 ──┘          ▲
                  └────────────────────┘ (07 em produção antes do deploy da 11)
```

A 05 não depende da migração e pode ser feita em paralelo com 02–04.

## Ordem de deploy e viradas

Duas viradas mexem no bot que já está em produção:

1. **Spec 03 (troca de host):** o agente passa a rodar no stack do agenda2. O webhook do
   bot atual é apontado para o host novo pelo script `set_webhook` que ainda existe, e o
   stack antigo é desligado. Passo a passo na spec 03.
2. **Spec 11 (várias instâncias do bot):** logo depois do deploy, conectar o bot atual ao
   estabelecimento dele via `PUT .../channels/telegram`. Passo a passo na spec 11.

Nas duas viradas, o Telegram guarda os updates pendentes e reenvia para a URL nova do
`setWebhook`. A documentação da Bot API diz que ele "desiste depois de um número razoável
de tentativas", então **as duas janelas precisam ficar em minutos**.

**Não conectar o bot de produção pelo painel antes do deploy da spec 11:** o webhook
passaria a apontar para uma rota que ainda não existe. Por isso a spec 12 (a tela) só
entra depois da 11.

## Riscos

- **Perder a `CHANNEL_SECRETS_KEY`** obriga a reconectar todos os bots, porque os tokens
  ficam ilegíveis. A chave precisa de backup fora da VPS.
- **Imagem maior:** LangGraph e os SDKs de LLM entram na imagem única, usada também por
  api, worker e mcp. Separar em outro target de build fica para quando o tamanho
  incomodar.
- **O histórico das conversas é perdido uma vez**, na spec 09 (a chave muda) e na spec 03
  (Redis novo). O TTL já é de 24h e expirar não é erro.

## Fora de escopo

- WhatsApp (API oficial e Evolution). Para depois: rotear pela URL serve para Evolution
  (um webhook por instância), mas não para a API oficial, que tem um webhook por app da
  Meta e roteia pelo `phone_number_id` do payload. Por isso nada foi generalizado agora;
  cada canal ganha a própria tabela no módulo `channels`.
- Identidade real do cliente (`request_contact`): o telefone sintético continua.
- Nome do estabelecimento no prompt e tools de dados do estabelecimento.
- Saúde do webhook (`getWebhookInfo`) no painel.
- Rotação da chave de cifra (`MultiFernet`).
- Achatar as settings do agente no `Settings` do backend, unificar os Redis e chamar as
  tools sem passar pelo MCP.
