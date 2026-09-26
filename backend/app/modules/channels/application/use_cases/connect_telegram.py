import logging
import secrets
import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.channels.application.authz import assert_can_manage
from app.modules.channels.application.ports.telegram_bot_api import (
    TelegramBotApiProtocol,
)
from app.modules.channels.application.ports.unit_of_work import (
    ChannelsUnitOfWorkProtocol,
)
from app.modules.channels.domain.entities import NewTelegramBot, TelegramBot
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)

logger = logging.getLogger(__name__)

_BOT_TAKEN_MESSAGE = "Este bot já está conectado a outro estabelecimento."


class TelegramBotConnector:
    def __init__(
        self,
        uow: ChannelsUnitOfWorkProtocol,
        bot_api: TelegramBotApiProtocol,
        webhook_base_url: str,
    ) -> None:
        """
        Args:
            uow (ChannelsUnitOfWorkProtocol):
                Unit of work dos canais.
            bot_api (TelegramBotApiProtocol):
                Cliente da Bot API do Telegram.
            webhook_base_url (str):
                Base HTTPS pública do webhook, sem `/` no fim.
        """

        self._uow = uow
        self._bot_api = bot_api
        self._webhook_base_url = webhook_base_url

    async def connect(
        self,
        actor: UserActor,
        establishment_id: uuid.UUID,
        bot_token: str,
    ) -> TelegramBot:
        """
        Valida o token, aponta o webhook do bot para o agente e grava o bot.

        Cada conexão gera um segredo de webhook novo, inclusive ao reconectar o mesmo
        bot. Se outro bot estava conectado, o webhook dele é removido (best-effort).

        As chamadas ao Telegram ficam dentro do UoW: se o `setWebhook` falhar, nada é
        gravado. Se o commit falhar depois do `setWebhook`, o webhook aponta para o
        agente sem bot gravado; o agente responde `404` e basta repetir a operação.

        Raises:
            ForbiddenError: o ator não pode gerenciar o bot do estabelecimento.
            InvalidBotTokenError: o Telegram recusou o token.
            TelegramApiError: o Telegram não respondeu ou deu erro.
            NotFoundError: o estabelecimento não existe.
            ConflictError: o bot já está conectado a outro estabelecimento.
        """

        assert_can_manage(actor, establishment_id)
        identity = await self._bot_api.get_me(bot_token)

        try:
            async with self._uow as uow:
                establishment = await uow.establishments.get_by_id_or_none(
                    establishment_id
                )
                if establishment is None:
                    raise NotFoundError("Estabelecimento não encontrado.")

                owner = await uow.telegram_bots.get_by_bot_id(identity.id)
                if owner is not None and owner.establishment_id != establishment_id:
                    raise ConflictError(_BOT_TAKEN_MESSAGE)

                current = await uow.telegram_bots.get_by_establishment(establishment_id)
                secret = secrets.token_urlsafe(32)
                await self._bot_api.set_webhook(
                    bot_token,
                    url=f"{self._webhook_base_url}/webhook/telegram/{establishment_id}",
                    secret_token=secret,
                )
                if current is not None and current.bot_id != identity.id:
                    await self._delete_old_webhook(current)

                return await uow.telegram_bots.save(
                    NewTelegramBot(
                        establishment_id=establishment_id,
                        bot_id=identity.id,
                        bot_username=identity.username,
                        bot_token=bot_token,
                        webhook_secret=secret,
                    )
                )
        except IntegrityError as exc:
            # Dois estabelecimentos conectando o mesmo bot ao mesmo tempo: a
            # `UNIQUE(bot_id)` barra o segundo.
            raise ConflictError(_BOT_TAKEN_MESSAGE) from exc

    async def _delete_old_webhook(self, old: TelegramBot) -> None:
        """Para o bot antigo de bater no agente, sem abortar a troca se falhar."""

        try:
            await self._bot_api.delete_webhook(
                old.bot_token, drop_pending_updates=False
            )
        except InvalidBotTokenError, TelegramApiError:
            logger.warning(
                "Não foi possível remover o webhook do bot antigo %s do "
                "estabelecimento %s.",
                old.bot_id,
                old.establishment_id,
                exc_info=True,
            )
