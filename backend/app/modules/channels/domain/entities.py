import uuid
from dataclasses import dataclass, field
from datetime import datetime

# Os segredos ficam fora do `repr`: um log ou traceback com a entidade não pode
# expor o token do bot nem o segredo do webhook.


@dataclass(frozen=True, slots=True)
class NewTelegramBot:
    establishment_id: uuid.UUID
    bot_id: int
    bot_username: str
    bot_token: str = field(repr=False)
    webhook_secret: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class TelegramBot:
    establishment_id: uuid.UUID
    bot_id: int
    bot_username: str
    bot_token: str = field(repr=False)
    webhook_secret: str = field(repr=False)
    created_at: datetime
    updated_at: datetime
