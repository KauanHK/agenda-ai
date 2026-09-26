import logging
import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.channels.application.authz import assert_can_manage
from app.modules.channels.application.ports.telegram_bot_api import (
    TelegramBotApiProtocol,
)
from app.modules.channels.application.ports.unit_of_work import (
    ChannelsUnitOfWorkProtocol,
)
from app.modules.channels.domain.exceptions import InvalidBotTokenError

logger = logging.getLogger(__name__)


class TelegramBotDisconnector:
    def __init__(
        self,
        uow: ChannelsUnitOfWorkProtocol,
        bot_api: TelegramBotApiProtocol,
    ) -> None:
        self._uow = uow
        self._bot_api = bot_api

    async def disconnect(self, actor: UserActor, establishment_id: uuid.UUID) -> None:
        """
        Remove o webhook do bot e apaga o bot do estabelecimento.

        Se o token foi revogado no @BotFather, não há webhook ativo e o bot é apagado
        mesmo assim. Qualquer outra falha do Telegram aborta sem apagar: senão o
        webhook continuaria entregando mensagens a um agente que responde `404`, sem
        nada no painel indicando o problema.

        Raises:
            ForbiddenError: o ator não pode gerenciar o bot do estabelecimento.
            NotFoundError: nenhum bot conectado ao estabelecimento.
            TelegramApiError: o Telegram não respondeu ou deu erro.
        """

        assert_can_manage(actor, establishment_id)

        async with self._uow as uow:
            bot = await uow.telegram_bots.get_by_establishment(establishment_id)
            if bot is None:
                raise NotFoundError("Nenhum bot do Telegram conectado.")

            try:
                await self._bot_api.delete_webhook(
                    bot.bot_token, drop_pending_updates=True
                )
            except InvalidBotTokenError:
                logger.info(
                    "Token do bot %s do estabelecimento %s revogado; apagando sem "
                    "remover o webhook.",
                    bot.bot_id,
                    establishment_id,
                )

            await uow.telegram_bots.delete(establishment_id)
