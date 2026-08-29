"""Compat: `MessagingTemplatesUpdater` agora vive em
`app.modules.messaging_templates.application.use_cases.update`. Re-export para imports
antigos."""

from app.modules.messaging_templates.application.use_cases.update import (
    MessagingTemplatesUpdater,
)

__all__ = ["MessagingTemplatesUpdater"]
