"""Compat: o repositório agora vive em
`app.modules.scheduling_notifications.adapters.db.repository`. Re-export para imports
antigos (consumido pelo worker Celery, que instancia a classe diretamente com a
sessão e chama `get_pending_due(limit=100)`)."""

from app.modules.scheduling_notifications.adapters.db.repository import (
    SchedulingNotificationsRepository,
)

__all__ = ["SchedulingNotificationsRepository"]
