"""Compat: os filtros agora vivem em
`app.modules.messaging_templates.application.dtos.filters`. Re-export para imports
antigos."""

from app.modules.messaging_templates.application.dtos.filters import (
    MessagingTemplateFilters,
)

__all__ = ["MessagingTemplateFilters"]
