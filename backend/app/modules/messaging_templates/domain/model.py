"""Compat: os models SQLAlchemy agora vivem em
`app.modules.messaging_templates.adapters.db.models`. Re-export para imports antigos."""

from app.modules.messaging_templates.adapters.db.models import (
    MessagingTemplate,
    ServiceMessagingTemplate,
)

__all__ = ["MessagingTemplate", "ServiceMessagingTemplate"]
