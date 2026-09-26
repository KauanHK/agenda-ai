import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.secret_box import decrypt, encrypt
from app.modules.channels.adapters.db.models import TelegramBot as TelegramBotModel
from app.modules.channels.domain.entities import NewTelegramBot, TelegramBot


class TelegramBotsRepository:
    """
    Bots do Telegram por estabelecimento.

    É o único lugar que cifra e decifra: a entidade carrega os segredos em claro e o
    model, cifrados.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_establishment(
        self,
        establishment_id: uuid.UUID,
    ) -> TelegramBot | None:
        row = await self._session.get(TelegramBotModel, establishment_id)
        return None if row is None else self._to_entity(row)

    async def get_by_bot_id(self, bot_id: int) -> TelegramBot | None:
        result = await self._session.execute(
            select(TelegramBotModel).where(TelegramBotModel.bot_id == bot_id)
        )
        row = result.scalars().one_or_none()
        return None if row is None else self._to_entity(row)

    async def save(self, bot: NewTelegramBot) -> TelegramBot:
        """Insere o bot do estabelecimento ou substitui o que já existia."""

        row = await self._session.get(TelegramBotModel, bot.establishment_id)
        if row is None:
            row = TelegramBotModel(establishment_id=bot.establishment_id)
            self._session.add(row)

        row.bot_id = bot.bot_id
        row.bot_username = bot.bot_username
        row.bot_token_encrypted = encrypt(bot.bot_token)
        row.webhook_secret_encrypted = encrypt(bot.webhook_secret)

        await self._session.flush()
        await self._session.refresh(row)
        return self._to_entity(row)

    async def delete(self, establishment_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(TelegramBotModel).where(
                TelegramBotModel.establishment_id == establishment_id
            )
        )

    def _to_entity(self, row: TelegramBotModel) -> TelegramBot:
        return TelegramBot(
            establishment_id=row.establishment_id,
            bot_id=row.bot_id,
            bot_username=row.bot_username,
            bot_token=decrypt(row.bot_token_encrypted),
            webhook_secret=decrypt(row.webhook_secret_encrypted),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
