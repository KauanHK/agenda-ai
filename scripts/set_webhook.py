"""Registra o webhook do Telegram apontando para uma URL pública.

Lê o `.env` (token do bot e segredo do webhook) e recebe a base pública como
argumento — em desenvolvimento, a URL de um túnel HTTPS
(`cloudflared tunnel --url http://localhost:8080`).

Uso:

    uv run python -m scripts.set_webhook https://meu-tunel.trycloudflare.com
    uv run python -m scripts.set_webhook https://agente.exemplo --drop-pending

O segredo do webhook vai no caminho e também no header
`X-Telegram-Bot-Api-Secret-Token` (`secret_token`), que a rota valida.
"""

import argparse
import asyncio
import json
from typing import Any

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
        "base_url",
        help="base pública HTTPS, sem barra final (ex.: https://x.trycloudflare.com)",
    )
    parser.add_argument(
        "--drop-pending",
        action="store_true",
        help="descarta os updates acumulados na fila do Telegram",
    )
    return parser.parse_args()


def _redact(text: str, secret: str) -> str:
    return text.replace(secret, "***")


def _print_result(label: str, response: httpx.Response, secret: str) -> None:
    print(f"\n{label}: HTTP {response.status_code}")
    body = json.dumps(response.json(), indent=2, ensure_ascii=False)
    print(_redact(body, secret))


async def _run(args: argparse.Namespace, settings: Settings) -> None:
    token = settings.telegram.bot_token.get_secret_value()
    secret = settings.telegram.webhook_secret.get_secret_value()
    webhook_url = f"{args.base_url.rstrip('/')}/webhook/telegram/{secret}"

    print(f"Webhook  : {_redact(webhook_url, secret)}")
    print("Updates  : message")
    print(f"Pendentes: {'descartar' if args.drop_pending else 'manter'}")

    async with httpx.AsyncClient(
        base_url=f"{_TELEGRAM_API_ROOT}/bot{token}", timeout=httpx.Timeout(10.0)
    ) as client:
        payload: dict[str, Any] = {
            "url": webhook_url,
            "secret_token": secret,
            "allowed_updates": ["message"],
            "drop_pending_updates": args.drop_pending,
        }
        _print_result("setWebhook", await client.post("/setWebhook", json=payload), secret)
        _print_result("getWebhookInfo", await client.get("/getWebhookInfo"), secret)


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
