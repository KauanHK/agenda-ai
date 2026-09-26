# 09 — Estado do agente por estabelecimento

**Repositório:** agenda2 · **Depende de:** 04 · **Estimativa:** ~90 linhas

## Objetivo

Fazer todo o estado e todas as dependências do turno trazerem o estabelecimento
explicitamente: histórico, cache de sessão, emissão de sessão, fuso e endereço de
resposta. O estabelecimento **continua vindo do env** (um só) nesta PR. A spec 11 só vai
trocar de onde ele vem.

## Contexto: as colisões

No Telegram, o `chat_id` de uma conversa privada é o id do usuário, igual em todos os
bots. Com dois estabelecimentos:

- `ConversationRef.thread_id = "telegram:{chat_id}"` mistura os históricos.
- O cache de sessão com chave `sha256(phone)`, sendo o telefone sintético derivado do
  `chat_id`, devolve o token do estabelecimento A para uma conversa com o bot B. O agente
  agendaria **no estabelecimento errado**.

## Mudanças

### Domínio (`app/modules/agent/domain/entities.py`)

- **Nova entidade `Establishment(id: UUID, timezone: ZoneInfo)`:** o que o agente precisa
  saber do estabelecimento. `ZoneInfo` é stdlib; validar o fuso na construção pega fuso
  inválido cedo.
- **`IncomingMessage`** ganha `establishment: Establishment`.
- **`ConversationRef`** ganha `establishment_id: UUID`, e
  `thread_id = "telegram:{establishment_id}:{channel_user_id}"`.
- **`BookingSession`** ganha `establishment_id`: a sessão sabe de qual estabelecimento é.

### Portas e casos de uso

- **`BookingSessionIssuerProtocol.issue(establishment_id, phone, name)`.** O
  `InProcessSessionIssuer` (spec 04) repassa o valor ao `CustomerSessionIssuer`, em vez
  de usar o fixo.
- **`SessionTokenCacheProtocol.get(establishment_id, phone)`.**
  - `put(session)` usa `session.establishment_id`.
  - Chave no Redis: `agente:session:{establishment_id}:{sha256(phone)}`.
- **`BookingSessionProvider.for_contact(contact, establishment_id)`.**
- **`OutboundMessengerProtocol.send_text(conversation: ConversationRef, text)` e
  `signal_typing(conversation)`**, no lugar de `Contact`.
  - `Contact` não diz por qual bot responder; `ConversationRef` diz (canal +
    estabelecimento + usuário).
  - O `TelegramMessenger` só usa `conversation.channel_user_id` por enquanto; a spec 11
    usa o `establishment_id` para escolher o bot.
- **`HandleIncomingMessage`:**
  - O relógio injetado passa a ser UTC.
  - O "agora" do prompt é `clock().astimezone(message.establishment.timezone)`.
  - Monta o `ConversationRef` com o estabelecimento da mensagem.
- **`TelegramWebhookHandler` e `parse_update`** recebem o `Establishment` e o colocam na
  `IncomingMessage` e no `ConversationRef`.

### Container

- Monta **um** `Establishment` a partir de `AGENT_AGENDABOT__ESTABLISHMENT_ID` e
  `_ESTABLISHMENT_TIMEZONE` e o fixa no `parse_update` (`functools.partial`). Esse é o
  único lugar que ainda sabe que existe um estabelecimento só.

## Fora de escopo

- De onde vem o estabelecimento (spec 11).
- Várias instâncias do bot e o token por estabelecimento (spec 11).

## Testes

- `ConversationRef.thread_id`: mesmo `chat_id` em dois estabelecimentos gera threads
  diferentes.
- Cache de sessão (`fakeredis`): `put` de uma sessão do estabelecimento A seguido de `get`
  com (B, mesmo telefone) devolve `None`.
- `BookingSessionProvider`: repassa o `establishment_id` ao emissor e ao cache.
- `HandleIncomingMessage`: com um relógio UTC fixo e um estabelecimento em
  `America/Manaus`, o contexto do prompt tem a hora de Manaus. Também confere que o
  messenger recebe o `ConversationRef` com o estabelecimento.
- `parse_update`: a mensagem sai com o estabelecimento recebido.
- Os fakes (`tests/modules/agent/fakes/`) acompanham as assinaturas novas.

## Critérios de aceite

- Em produção, o bot continua atendendo normalmente.

## Deploy

- Deploy normal. **Efeito conhecido:** a chave das conversas muda, então o histórico em
  andamento é perdido uma vez (TTL de 24h). As entradas antigas do cache de sessão
  expiram sozinhas em até `MCP_SESSION_TOKEN_EXPIRES_MINUTES`.
