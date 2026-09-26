# 01 — Não logar a URL com o token do bot

**Repositório:** `agente-agenda` (antes da migração) · **Depende de:** — · **Estimativa:** ~5 linhas

## Objetivo

Parar de gravar o token do bot nos logs de produção.

## Contexto

A Bot API exige o token no caminho (`/bot<token>/<método>`). O `httpx` registra toda
requisição em INFO com a URL completa, e `configure_logging` coloca o root em
`OBSERVABILITY__LOG_LEVEL` (padrão `INFO`). Reproduzido:

```
{"level": "INFO", "logger": "httpx", "msg": "HTTP Request: POST https://api.telegram.org/bot123:SECRET-TOKEN/sendMessage \"HTTP/1.1 200 OK\""}
```

Os cuidados que já existem (`from None` nos erros, token só dentro de
`infrastructure/telegram/`) não cobrem isso. Quando os tokens forem dos clientes, um log
vazado dá controle dos bots deles.

## Mudanças

- `src/logging_config.py::configure_logging`: depois do `basicConfig`, subir os loggers
  `httpx` e `httpcore` para `WARNING`, independente do nível configurado. Um comentário
  curto explica o motivo (URL com segredo).

Isso fica no `configure_logging`, e não no client, porque o logger do `httpx` é global:
qualquer client criado depois herda o nível.

## Testes

- Com `configure_logging("DEBUG")`, uma requisição por `httpx.MockTransport` para
  `https://api.telegram.org/bot123:SECRET/sendMessage` não gera nenhum record (via
  `caplog`) cuja mensagem contenha `SECRET`.
- O root continua no nível pedido: um `logger.info` da aplicação ainda sai.

## Critérios de aceite

- O comando de reprodução acima não imprime mais nada.
- `ruff`, `mypy` e `pytest` verdes.

## Deploy

Deploy normal do agente, sem mudança de env.
