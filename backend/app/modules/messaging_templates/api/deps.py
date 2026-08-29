"""Compat: as dependências HTTP agora vivem em
`app.modules.messaging_templates.adapters.http.dependencies`. Re-export para imports
antigos."""

from app.modules.messaging_templates.adapters.http.dependencies import (
    MessagingTemplatesUnitOfWorkDep,
    PaginationFiltersDep,
)

__all__ = ["MessagingTemplatesUnitOfWorkDep", "PaginationFiltersDep"]
