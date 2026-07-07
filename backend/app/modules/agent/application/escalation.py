import asyncio
import logging

from app.integrations import evolution

logger = logging.getLogger(__name__)

_MOTIVO_LABELS = {
    "COMPLAINT": "Reclamação do cliente",
    "MAX_ATTEMPTS": "Várias tentativas sem resolver",
    "AGGRESSIVE": "Linguagem agressiva do cliente",
    "OUT_OF_SCOPE": "Solicitação fora do escopo do agente",
}


class OwnerNotifier:
    async def notify(
        self,
        owner_phone: str | None,
        client_name: str | None,
        client_phone: str,
        motivo: str,
        resumo: str,
    ) -> None:
        if not owner_phone:
            logger.warning(
                "Escalation triggered but establishment has no owner_phone. "
                "motivo=%s resumo=%s client=%s",
                motivo,
                resumo,
                client_phone,
            )
            return

        label = _MOTIVO_LABELS.get(motivo, motivo)
        display_name = client_name or client_phone
        text = (
            f"Atenção necessária\n\n"
            f"Cliente: {display_name}\n"
            f"Motivo: {label}\n\n"
            f"Resumo: {resumo}"
        )

        try:
            await asyncio.to_thread(evolution.send_text, phone=owner_phone, text=text)
        except evolution.EvolutionAPIError as exc:
            logger.error("Failed to send escalation notification: %s", exc)
