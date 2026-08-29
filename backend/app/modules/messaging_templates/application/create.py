"""Compat: `MessagingTemplatesCreator` agora vive em
`app.modules.messaging_templates.application.use_cases.create`. Re-export para imports
antigos."""

from app.modules.messaging_templates.application.use_cases.create import (
    MessagingTemplatesCreator,
)

__all__ = ["MessagingTemplatesCreator"]
