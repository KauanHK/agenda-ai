"""Compat: os schemas HTTP agora vivem em
`app.modules.messaging_templates.adapters.http.schemas`. Re-export para imports
antigos."""

from app.modules.messaging_templates.adapters.http.schemas import (
    MessagingTemplateBase,
    MessagingTemplateCreate,
    MessagingTemplateListItem,
    MessagingTemplateRead,
    MessagingTemplateUpdate,
    ServiceMessagingTemplateRead,
    ServiceRef,
)

__all__ = [
    "MessagingTemplateBase",
    "MessagingTemplateCreate",
    "MessagingTemplateListItem",
    "MessagingTemplateRead",
    "MessagingTemplateUpdate",
    "ServiceMessagingTemplateRead",
    "ServiceRef",
]
