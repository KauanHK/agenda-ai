import httpx

from app.core.settings import settings


class EvolutionAPIError(Exception):
    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"{status_code}: {body}")
        self.status_code = status_code
        self.body = body


# Sync: intended for use from Celery worker tasks only.
def send_text(phone: str, text: str) -> None:
    url = f"{settings.EVOLUTION_URL}/message/sendText/{settings.EVOLUTION_INSTANCE}"
    headers = {"apikey": settings.EVOLUTION_APIKEY}
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json={"number": phone, "text": text}, headers=headers)
    except httpx.RequestError as exc:
        raise EvolutionAPIError(0, str(exc)) from exc
    if not response.is_success:
        raise EvolutionAPIError(response.status_code, response.text)
