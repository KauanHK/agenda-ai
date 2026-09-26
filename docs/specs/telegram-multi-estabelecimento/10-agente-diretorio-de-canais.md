# 10 — Diretório de canais do agente

**Repositório:** agenda2 · **Depende de:** 05, 09 · **Estimativa:** ~60 linhas

## Objetivo

Dar ao agente uma forma de descobrir, a partir do `establishment_id`, qual bot atende
aquele estabelecimento: token, segredo do webhook e o `Establishment` (id e fuso). É o
que as rotas e o envio da spec 11 consomem. Nesta PR, nada usa ainda.

## Mudanças

### Domínio

- `TelegramChannel(establishment: Establishment, bot_token: str, webhook_secret: str)`,
  com `field(repr=False)` nos dois segredos.
- `ChannelLookupError(AgentError)`: o diretório não conseguiu consultar (banco fora). A
  spec 11 transforma isso em `503` no webhook, para o Telegram reenviar.

### Porta

- `application/ports/channel_directory.py` → `TelegramChannelDirectoryProtocol`:
  - `get(establishment_id) -> TelegramChannel | None`
  - `None` significa "não atende": sem bot conectado, estabelecimento inexistente,
    inativo ou excluído (`deleted_at`).

### Adapter

- `adapters/channels/telegram_directory.py` → `DbTelegramChannelDirectory`:
  - Usa o `ChannelsUnitOfWork` da spec 05, que tem `telegram_bots` e `establishments`.
  - Monta o `TelegramChannel` com o `timezone` do estabelecimento.
  - `SQLAlchemyError` e `OSError` viram `ChannelLookupError`.

**Sem cache.** Cada update custa uma busca por chave primária e uma decifragem Fernet (na
casa dos microssegundos). Com cache, reconectar ou desconectar passaria a demorar o TTL
para valer, e um segredo trocado recusaria updates legítimos durante esse tempo. Se o
custo aparecer em medição, o cache entra aqui, atrás da porta.

A mesma conta vale para a rota pública: um UUID aleatório custa uma busca por chave
primária que não encontra nada.

## Testes

Com o UoW falso:

- Bot conectado e estabelecimento ativo: devolve o `TelegramChannel` com o fuso certo.
- Sem bot → `None`; estabelecimento inativo → `None`; estabelecimento excluído → `None`.
- Falha do UoW (`SQLAlchemyError`) → `ChannelLookupError`.
- `repr(channel)` não contém o token nem o segredo.

## Critérios de aceite

- Porta e adapter prontos, com o teste de arquitetura do agente verde (o domínio não
  importa `channels` nem SQLAlchemy).

## Deploy

Deploy normal. O código ainda não está ligado a nenhuma rota.
