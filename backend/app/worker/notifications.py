import asyncio
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import app.db.models  # noqa: F401
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery
from app.db.session import db
from app.integrations.evolution import EvolutionAPIError, send_text
from app.modules.clients.domain.model import Client
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.schedulings.domain.model import Scheduling
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.infra.repository import (
    SchedulingNotificationsRepository,
)
from app.modules.services.domain.model import Service

_TZ = ZoneInfo("America/Sao_Paulo")


@celery.task(name="beat_dispatch_notifications")
def beat_dispatch_notifications() -> None:
    asyncio.run(_dispatch_pending())


async def _dispatch_pending() -> None:
    db.init()
    async with db.create_session() as session:
        repo = SchedulingNotificationsRepository(session)
        notifications = await repo.get_pending_due(limit=100)
        for notification in notifications:
            send_notification.delay(str(notification.id))


@celery.task(name="send_notification")
def send_notification(notification_id: str) -> None:
    asyncio.run(_run_send(uuid.UUID(notification_id)))


async def _run_send(notification_id: uuid.UUID) -> None:
    db.init()
    async with db.create_session() as session:
        async with session.begin():
            await _send_notification(notification_id, session)


async def _send_notification(notification_id: uuid.UUID, session: AsyncSession) -> None:
    result = await session.execute(
        select(SchedulingNotification)
        .where(SchedulingNotification.id == notification_id)
        .where(SchedulingNotification.status == NotificationStatus.pending)
        .with_for_update(skip_locked=True)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        return

    scheduling = await session.get(Scheduling, notification.scheduling_id)
    if scheduling is None:
        notification.status = NotificationStatus.failed
        notification.last_error = "Agendamento não encontrado"
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(UTC)
        return

    client = await session.get(Client, scheduling.client_id)
    service = await session.get(Service, scheduling.service_id)
    template = await session.get(MessagingTemplate, notification.template_id)

    if client is None or service is None or template is None:
        notification.status = NotificationStatus.failed
        notification.last_error = "Dados relacionados não encontrados"
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(UTC)
        return

    starts_local = scheduling.starts_at.astimezone(_TZ)
    try:
        rendered = template.content.format_map({
            "cliente": client.name,
            "servico": service.name,
            "data": starts_local.strftime("%d/%m/%Y"),
            "hora": starts_local.strftime("%H:%M"),
        })
    except KeyError as exc:
        notification.status = NotificationStatus.failed
        notification.last_error = f"Variável desconhecida no template: {exc}"
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(UTC)
        return

    notification.content_at_send = rendered
    now = datetime.now(UTC)
    try:
        send_text(client.phone, rendered)
        notification.status = NotificationStatus.sent
        notification.sent_at = now
        notification.last_attempt_at = now
        notification.attempts += 1
    except EvolutionAPIError as exc:
        notification.status = NotificationStatus.failed
        notification.last_error = str(exc)
        notification.attempts += 1
        notification.last_attempt_at = now
