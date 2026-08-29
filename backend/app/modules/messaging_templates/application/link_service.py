"""Compat: `MessagingTemplatesServiceLinker` agora vive em
`app.modules.messaging_templates.application.use_cases.link_service`. Re-export para
imports antigos."""

from app.modules.messaging_templates.application.use_cases.link_service import (
    MessagingTemplatesServiceLinker,
)

__all__ = ["MessagingTemplatesServiceLinker"]
