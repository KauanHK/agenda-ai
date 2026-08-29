"""Compat: os filtros agora vivem em
`app.modules.clients.application.dtos.filters`. Re-export para imports antigos."""

from app.modules.clients.application.dtos.filters import ClientFilters

__all__ = ["ClientFilters"]
