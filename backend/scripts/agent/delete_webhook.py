"""Remove o webhook do Telegram registrado pelo bot.

Lê o `.env` (só o token do bot). Desfaz o que `scripts/agent/set_webhook.py` fez — útil
para voltar ao polling ou trocar de túnel.

Uso:

    uv run python -m scripts.agent.delete_webhook
    uv run python -m scripts.agent.delete_webhook --drop-pending
"""

import argparse
import asyncio
import json

from pydantic import ValidationError

from app.modules.agent.settings import Settings
from app.modules.channels.adapters.telegram.bot_api import (
    TelegramBotApi,
    build_bot_api_client,
)
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--drop-pending",
        action="store_true",
        help="descarta os updates acumulados na fila do Telegram",
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace, settings: Settings) -> int:
    token = settings.telegram.bot_token.get_secret_value()
    async with build_bot_api_client(settings.telegram.api_root) as client:
        bot_api = TelegramBotApi(client)
        try:
            await bot_api.delete_webhook(token, drop_pending_updates=args.drop_pending)
            info = await bot_api.get_webhook_info(token)
        except (InvalidBotTokenError, TelegramApiError) as error:
            print(f"Falhou: {error}")
            return 1
    print("Webhook removido.\n\ngetWebhookInfo:")
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    args = _parse_args()
    try:
        settings = Settings()
    except ValidationError as error:
        print("Configuração inválida — preencha o `.env` (veja `.env.example`):\n")
        print(error)
        return 2
    return asyncio.run(_run(args, settings))


if __name__ == "__main__":
    raise SystemExit(main())
