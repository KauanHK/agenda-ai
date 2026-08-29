"""Manutenção das notificações de um agendamento alterado pelo cliente."""

import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling_notifications.adapters.db.models import (
    SchedulingNotification,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


async def cancel_pending_notifications(
    session: AsyncSession,
    scheduling_id: uuid.UUID,
) -> None:
    """
    Cancela as notificações ainda não enviadas de um agendamento.

    Chamado ao cancelar e ao reagendar — nos dois casos as mensagens já programadas
    ficariam erradas (avisando de um horário que não existe mais).

    Args:
        session (AsyncSession): A sessão da transação em curso.
        scheduling_id (uuid.UUID): O agendamento afetado.
    """

    await session.execute(
        sa.update(SchedulingNotification)
        .where(
            SchedulingNotification.scheduling_id == scheduling_id,
            SchedulingNotification.status == NotificationStatus.pending,
        )
        .values(status=NotificationStatus.cancelled)
    )
