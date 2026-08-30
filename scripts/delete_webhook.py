"""Remove o webhook do Telegram registrado pelo bot.

Lê o `.env` (só o token do bot). Desfaz o que `scripts/set_webhook.py` fez — útil
para voltar ao polling ou trocar de túnel.

Uso:

    uv run python -m scripts.delete_webhook
    uv run python -m scripts.delete_webhook --drop-pending
"""

import argparse
import asyncio
import json

import httpx
from pydantic import ValidationError

from src.settings import Settings

_TELEGRAM_API_ROOT = "https://api.telegram.org"


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


def _print_result(label: str, response: httpx.Response) -> None:
    print(f"\n{label}: HTTP {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


async def _run(args: argparse.Namespace, settings: Settings) -> None:
    token = settings.telegram.bot_token.get_secret_value()
    async with httpx.AsyncClient(
        base_url=f"{_TELEGRAM_API_ROOT}/bot{token}", timeout=httpx.Timeout(10.0)
    ) as client:
        response = await client.post(
            "/deleteWebhook", json={"drop_pending_updates": args.drop_pending}
        )
        _print_result("deleteWebhook", response)
        _print_result("getWebhookInfo", await client.get("/getWebhookInfo"))


def main() -> int:
    args = _parse_args()
    try:
        settings = Settings()
    except ValidationError as error:
        print("Configuração inválida — preencha o `.env` (veja `.env.example`):\n")
        print(error)
        return 2
    asyncio.run(_run(args, settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
