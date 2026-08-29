"""Compat: `MessagingTemplatesDeleter` agora vive em
`app.modules.messaging_templates.application.use_cases.delete`. Re-export para imports
antigos."""

from app.modules.messaging_templates.application.use_cases.delete import (
    MessagingTemplatesDeleter,
)

__all__ = ["MessagingTemplatesDeleter"]
