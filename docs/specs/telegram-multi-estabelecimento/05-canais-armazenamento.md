# 05 — Guardar o bot cifrado por estabelecimento

**Repositório:** agenda2 · **Depende de:** — (pode andar em paralelo com 02–04) ·
**Estimativa:** ~140 linhas

## Objetivo

Criar o módulo `channels` com a persistência do bot do Telegram de cada estabelecimento:
tabela, entidade, repositório e unit of work. O token e o segredo do webhook ficam
cifrados. Nenhuma rota nesta PR.

## Modelo

Tabela `telegram_bots`:

| Coluna | Tipo | Regra |
|---|---|---|
| `establishment_id` | UUID | PK, FK `establishments.id` `ON DELETE CASCADE`. **Um bot por estabelecimento.** |
| `bot_id` | BIGINT | `UNIQUE NOT NULL`: o id numérico que o `getMe` devolve. **Um estabelecimento por bot.** |
| `bot_username` | VARCHAR(64) | `NOT NULL` |
| `bot_token_encrypted` | TEXT | `NOT NULL` |
| `webhook_secret_encrypted` | TEXT | `NOT NULL` |
| `created_at` / `updated_at` | TIMESTAMPTZ | padrão dos outros módulos |

O segredo do webhook também é cifrado. Quem tem esse segredo consegue forjar updates e
fazer o agente agir como qualquer usuário do Telegram naquele estabelecimento.

Canais futuros (WhatsApp) ganham a própria tabela neste módulo. Não haverá tabela
genérica de "canal" com JSON.

## Mudanças

- **`app/core/security/secret_box.py`:** `encrypt(plaintext) -> str` e
  `decrypt(ciphertext) -> str` sobre `cryptography.fernet.Fernet`, com a chave
  `CHANNEL_SECRETS_KEY`.
  - Um `InvalidToken` vira um erro de configuração explícito ("chave de cifra não
    confere"); nunca devolve texto vazio.
  - Fica em `core/security` porque o próximo canal vai usar a mesma função.
- **`app/core/settings.py`:** `CHANNEL_SECRETS_KEY: str`. Uma chave inválida para o
  Fernet falha no boot, não na primeira leitura.
- **`backend/pyproject.toml`:** `cryptography` vira dependência **direta** da base. Hoje
  ela só está no lock como dependência indireta, e o backend não deve depender disso.
- **Módulo `app/modules/channels/`**, seguindo o layout de `operating_hours`:
  - `domain/entities.py`:
    - `TelegramBot`: `establishment_id`, `bot_id`, `bot_username`, `bot_token`,
      `webhook_secret`, `created_at`, `updated_at`;
    - `NewTelegramBot`, com os mesmos campos menos os timestamps.
    - Os campos de segredo usam `field(repr=False)`, para um `repr` em log ou traceback
      não expor o token.
  - `application/ports/repositories.py` e `unit_of_work.py`: protocolos.
  - `adapters/db/models.py`, com o model registrado em `app/db/models.py`, que é o que o
    Alembic e o `conftest` importam.
  - `adapters/db/repository.py` → `TelegramBotsRepository`:
    - `get_by_establishment(establishment_id) -> TelegramBot | None`
    - `get_by_bot_id(bot_id) -> TelegramBot | None`
    - `save(bot: NewTelegramBot) -> TelegramBot`: insere ou substitui a linha do
      estabelecimento.
    - `delete(establishment_id) -> None`
    - Cifra e decifra **só aqui**: a entidade tem texto em claro e o model tem o texto
      cifrado.
  - `adapters/db/unit_of_work.py` → `ChannelsUnitOfWork`, com `telegram_bots` e
    `establishments` (o `EstablishmentsRepository` que já existe, como o
    `BookingUnitOfWork` faz). As specs 07 e 10 precisam checar se o estabelecimento
    existe, está ativo e qual é o fuso.
  - `adapters/db/factories.py` → `make_unit_of_work()`.
- **Migration Alembic** criando a tabela.
- **`.env.example`:** `CHANNEL_SECRETS_KEY`, com o comando para gerar:
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`,
  e o aviso de que **perder a chave obriga a reconectar todos os bots**.

## Testes

- `secret_box`:
  - cifrar e decifrar devolve o texto original;
  - o texto cifrado não contém o original;
  - decifrar com outra chave levanta o erro de configuração.
- `TelegramBot` e `NewTelegramBot`: `repr()` não contém o token nem o segredo.
- Repositório, no padrão dos testes de repositório existentes: o model gravado tem os
  campos cifrados e a entidade lida volta decifrada.

## Critérios de aceite

- `alembic upgrade head` e `alembic downgrade -1` funcionam no banco local.
- Sem a `CHANNEL_SECRETS_KEY`, a API não sobe e a mensagem de erro nomeia a variável.

## Deploy

1. Gerar a `CHANNEL_SECRETS_KEY` e colocar em `/opt/agenda-bot/.env` **antes** do merge,
   porque a API não sobe sem ela.
2. Guardar a chave fora da VPS.
3. A migration roda no serviço `migrate`.
