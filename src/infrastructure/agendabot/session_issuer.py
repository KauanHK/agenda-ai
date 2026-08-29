"""Emissão da sessão do cliente via a API HTTP do AgendaBot."""

import asyncio
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta

import httpx

from src.domain.entities import BookingSession
from src.domain.exceptions import BookingSessionError, ClientBlockedError


class AgendaBotSessionIssuer:
    """Troca o telefone do cliente por uma sessão autenticada no AgendaBot.

    Implementa `BookingSessionIssuerProtocol`. Toda falha de transporte ou de
    status HTTP é traduzida aqui num erro de domínio: nenhum `httpx.HTTPError`
    sobe deste adapter.

    Retry só nos casos idempotentes-seguros — erro de conexão e `5xx` —, com
    backoff exponencial. Um `4xx` nunca é repetido.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        establishment_id: uuid.UUID,
        clock: Callable[[], datetime],
        max_attempts: int = 3,
        backoff_base_seconds: float = 0.2,
    ) -> None:
        self._client = client
        self._path = f"/api/agent/{establishment_id}/sessions"
        self._clock = clock
        self._max_attempts = max_attempts
        self._backoff_base_seconds = backoff_base_seconds

    async def issue(self, phone: str, name: str | None) -> BookingSession:
        """Emite a sessão do cliente a partir do telefone."""
        payload: dict[str, str] = {"phone": phone}
        if name:
            payload["name"] = name

        last_cause: Exception | None = None
        for attempt in range(self._max_attempts):
            if attempt:
                await asyncio.sleep(self._backoff_base_seconds * 2 ** (attempt - 1))
            try:
                response = await self._client.post(self._path, json=payload)
            except httpx.ConnectError as exc:
                last_cause = exc
                continue
            except httpx.HTTPError as exc:
                raise BookingSessionError("Falha de transporte ao emitir a sessão.") from exc

            status = response.status_code
            if status == httpx.codes.CREATED:
                return self._to_session(response, issued_for=phone)
            if status == httpx.codes.FORBIDDEN:
                raise ClientBlockedError(f"Cliente inativo no estabelecimento (HTTP {status}).")
            if status >= httpx.codes.INTERNAL_SERVER_ERROR:
                last_cause = BookingSessionError(f"AgendaBot indisponível (HTTP {status}).")
                continue
            raise BookingSessionError(f"Emissão de sessão recusada (HTTP {status}).")

        raise BookingSessionError(
            "Emissão de sessão falhou após esgotar as tentativas."
        ) from last_cause

    def _to_session(self, response: httpx.Response, *, issued_for: str) -> BookingSession:
        """Converte o corpo `201` na entidade de sessão, calculando a expiração."""
        try:
            body = response.json()
            client = body["client"]
            return BookingSession(
                token=body["session_token"],
                phone=issued_for,
                client_id=uuid.UUID(client["id"]),
                client_name=client["name"],
                expires_at=self._clock() + timedelta(minutes=body["expires_in_minutes"]),
                is_new_client=bool(body["is_new_client"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise BookingSessionError("Resposta de emissão de sessão malformada.") from exc
