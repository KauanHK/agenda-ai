"""Compat: `MessagingTemplatesActivator` agora vive em
`app.modules.messaging_templates.application.use_cases.activate`. Re-export para
imports antigos."""

from app.modules.messaging_templates.application.use_cases.activate import (
    MessagingTemplatesActivator,
)

__all__ = ["MessagingTemplatesActivator"]
