"""Compat: `MessagingTemplatesReader` agora vive em
`app.modules.messaging_templates.application.use_cases.read`. Re-export para imports
antigos."""

from app.modules.messaging_templates.application.use_cases.read import (
    MessagingTemplatesReader,
)

__all__ = ["MessagingTemplatesReader"]
