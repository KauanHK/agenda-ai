"""Registra o webhook do Telegram apontando para uma URL pública.

Lê o `.env` (token do bot e segredo do webhook) e recebe a base pública como
argumento — em desenvolvimento, a URL de um túnel HTTPS
(`cloudflared tunnel --url http://localhost:8080`). Em produção o mesmo
registro é feito pela rota `POST /admin/telegram/webhook` (ver `docs/09`).

Uso:

    uv run python -m scripts.agent.set_webhook https://meu-tunel.trycloudflare.com
    uv run python -m scripts.agent.set_webhook https://agente.exemplo --drop-pending

O segredo do webhook vai no caminho e também no header
`X-Telegram-Bot-Api-Secret-Token` (`secret_token`), que a rota valida.
"""

import argparse
import asyncio
import json

from pydantic import ValidationError

from app.modules.agent.container import webhook_url
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
        "base_url",
        help="base pública HTTPS, sem barra final (ex.: https://x.trycloudflare.com)",
    )
    parser.add_argument(
        "--drop-pending",
        action="store_true",
        help="descarta os updates acumulados na fila do Telegram",
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace, settings: Settings) -> int:
    token = settings.telegram.bot_token.get_secret_value()
    secret = settings.telegram.webhook_secret.get_secret_value()
    url = webhook_url(args.base_url, secret)
    print(f"Webhook  : {url.replace(secret, '***')}")
    print("Updates  : message")
    print(f"Pendentes: {'descartar' if args.drop_pending else 'manter'}")

    async with build_bot_api_client(settings.telegram.api_root) as client:
        bot_api = TelegramBotApi(client)
        try:
            await bot_api.set_webhook(
                token,
                url=url,
                secret_token=secret,
                drop_pending_updates=args.drop_pending,
            )
            info = await bot_api.get_webhook_info(token)
        except (InvalidBotTokenError, TelegramApiError) as error:
            print(f"\nFalhou: {error}")
            return 1
    print("\ngetWebhookInfo:")
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
