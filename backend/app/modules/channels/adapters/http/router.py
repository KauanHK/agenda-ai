import uuid

from fastapi import APIRouter

from app.api.deps.auth import ActorDep
from app.core.exceptions import ExternalServiceError, ValidationAppError
from app.modules.channels.adapters.http.dependencies import (
    TelegramBotConnectorDep,
    TelegramBotReaderDep,
)
from app.modules.channels.adapters.http.schemas import (
    TelegramChannelConnect,
    TelegramChannelRead,
)
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)

router = APIRouter()


@router.get("", response_model=TelegramChannelRead)
async def get_telegram_channel(
    establishment_id: uuid.UUID,
    reader: TelegramBotReaderDep,
    actor: ActorDep,
) -> TelegramChannelRead:
    bot = await reader.get(actor, establishment_id)
    return TelegramChannelRead.from_bot(bot)


@router.put("", response_model=TelegramChannelRead)
async def connect_telegram_channel(
    establishment_id: uuid.UUID,
    data: TelegramChannelConnect,
    connector: TelegramBotConnectorDep,
    actor: ActorDep,
) -> TelegramChannelRead:
    try:
        bot = await connector.connect(
            actor, establishment_id, data.bot_token.get_secret_value()
        )
    except InvalidBotTokenError as exc:
        raise ValidationAppError(
            "Token do bot inválido. Confira com o @BotFather."
        ) from exc
    except TelegramApiError as exc:
        raise ExternalServiceError(
            "Não foi possível falar com o Telegram. Tente novamente."
        ) from exc
    return TelegramChannelRead.from_bot(bot)
