"""Compat: o repositório agora vive em
`app.modules.messaging_templates.adapters.db.repository`. Re-export para imports
antigos (consumido por app.modules.scheduling_notifications e pelo worker Celery)."""

from app.modules.messaging_templates.adapters.db.repository import (
    MessagingTemplatesRepository,
)

__all__ = ["MessagingTemplatesRepository"]
