# 12 — Card do Telegram no painel

**Repositório:** agenda2 (`frontend/`) · **Depende de:** 08, e 11 em produção ·
**Estimativa:** ~150 linhas de TSX

## Objetivo

Na tela Configurações ("Dados do estabelecimento e integrações"), um card "Telegram"
para ver o status do bot, conectar colando o token e desconectar.

**Entra só depois da spec 11 estar em produção.** Antes disso, conectar um bot aponta o
webhook para uma rota que o agente ainda não tem.

## Comportamento

**Quem vê o quê:**
- Todos os membros do estabelecimento veem o status.
- Conectar, trocar o token e desconectar ficam disponíveis para
  `user.is_global_admin || establishment_admin do estabelecimento ativo`.
- O `isAdmin` de `Settings.tsx` hoje só olha memberships; o card usa essa condição
  ampliada, sem mudar o resto da tela.

**Estados:**

| Estado | Mostra |
|---|---|
| Carregando | esqueleto ou "carregando…" |
| Desconectado | Passos curtos: "1. Crie um bot no @BotFather (`/newbot`). 2. Copie o token. 3. Cole aqui." Para quem pode editar, campo `password` + "Conectar". Para os demais, "Nenhum bot conectado." |
| Conectado | Badge "Conectado", `@bot_username` com link para `https://t.me/{username}`, "desde dd/mm/aaaa". Para quem pode editar: "Trocar token" (abre o mesmo campo) e "Desconectar" (com `window.confirm`, como em `Team.tsx`) |

**Erros:** o `ApiError` do client lê `detail`, mas as `AppError` do backend respondem com
`message`. Por isso o card traduz pelo **status**:

| Status | Mensagem |
|---|---|
| 422 | "Token inválido. Confira o token com o @BotFather." |
| 409 | "Este bot já está conectado a outro estabelecimento." |
| 502 | "O Telegram não respondeu. Tente novamente em instantes." |
| outros | toast genérico de erro, como nas outras telas |

Depois de conectar ou trocar, o campo do token é limpo. O token nunca fica em estado
persistido (`localStorage`) e nunca aparece em tela depois de enviado.

## Mudanças

- **`src/api/types.ts`:** `TelegramChannelRead` (`connected`, `bot_id`, `bot_username`,
  `connected_at`).
- **`src/api/channels.ts`:** `getTelegramChannel(eid)`, `connectTelegram(eid, botToken)`
  e `disconnectTelegram(eid)`, no padrão de `operating-hours.ts`. Reexportar em
  `src/api/index.ts`, se esse for o padrão.
- **`src/screens/TelegramChannelCard.tsx`:** o card, com `Card`, `Input`, `Button` e
  `Badge` de `components/ui`.
- **`src/screens/Settings.tsx`:** renderiza o card na área de integrações, antes do card
  do Google Calendar.

## Testes e verificação

- O frontend não tem suíte de testes hoje. A verificação é manual, no ambiente local com
  um bot de teste e o túnel:
  - desconectado → conectar com token inválido (mensagem de 422) → token válido (vira
    "Conectado", `@username` certo) → mandar mensagem no Telegram e receber resposta →
    trocar token → desconectar (volta ao estado inicial);
  - logado como `member`: só status, sem campo nem botões;
  - logado como `global_admin` sem membership: consegue conectar.
- `npm run build` sem erro de tipo.

## Critérios de aceite

- Os fluxos acima funcionando no ambiente local.
- Nenhuma requisição de `GET` devolve ou mostra o token (conferido no DevTools).

## Deploy

Deploy normal do frontend, depois da spec 11 em produção.
