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

    Retry só nos casos idempotentes-seguros — falha de conexão, timeout
    (`connect` / `read` / `write` / `pool`) e `5xx` —, com backoff exponencial.
    Um `4xx` nunca é repetido. Repetir a emissão é seguro: o AgendaBot resolve o
    cliente pelo telefone e devolve um token novo, sem duplicar cadastro.
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

        return await self._issue_with_retry(payload, issued_for=phone)

    async def _issue_with_retry(
        self, payload: dict[str, str], *, issued_for: str
    ) -> BookingSession:
        """Repete `_attempt` com backoff exponencial até obter a sessão ou esgotar."""
        last_cause: Exception | None = None
        for attempt in range(self._max_attempts):
            await self._backoff(attempt)
            outcome = await self._attempt(payload, issued_for=issued_for)
            if isinstance(outcome, BookingSession):
                return outcome
            last_cause = outcome

        raise BookingSessionError(
            "Emissão de sessão falhou após esgotar as tentativas."
        ) from last_cause

    async def _backoff(self, attempt: int) -> None:
        """Espera o backoff exponencial antes da tentativa (nada antes da primeira)."""
        if attempt:
            await asyncio.sleep(self._backoff_base_seconds * 2 ** (attempt - 1))

    async def _attempt(
        self, payload: dict[str, str], *, issued_for: str
    ) -> BookingSession | Exception:
        """Executa uma tentativa: retorna a sessão ou o erro repetível a guardar.

        Erros de transporte não repetíveis são levantados como `BookingSessionError`.
        """
        try:
            response = await self._client.post(self._path, json=payload)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            # `TimeoutException` cobre connect/read/write/pool — todos repetíveis
            # aqui (a emissão é reentrante).
            return exc
        except httpx.HTTPError as exc:
            raise BookingSessionError("Falha de transporte ao emitir a sessão.") from exc

        return self._interpret_response(response, issued_for=issued_for)

    def _interpret_response(
        self, response: httpx.Response, *, issued_for: str
    ) -> BookingSession | BookingSessionError:
        """Traduz o status HTTP na sessão emitida, num erro terminal ou num erro repetível.

        Retorna a `BookingSession` no `201` ou um `BookingSessionError` quando o
        status é `5xx` (repetível). Um `4xx` sempre levanta exceção aqui.
        """
        status = response.status_code
        if status == httpx.codes.CREATED:
            return self._to_session(response, issued_for=issued_for)
        if status == httpx.codes.FORBIDDEN:
            raise ClientBlockedError(f"Cliente inativo no estabelecimento (HTTP {status}).")
        if status >= httpx.codes.INTERNAL_SERVER_ERROR:
            return BookingSessionError(f"AgendaBot indisponível (HTTP {status}).")
        raise BookingSessionError(f"Emissão de sessão recusada (HTTP {status}).")

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
