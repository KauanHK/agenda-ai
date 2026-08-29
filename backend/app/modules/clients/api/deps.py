"""Compat: as dependências HTTP agora vivem em
`app.modules.clients.adapters.http.dependencies`. Re-export para imports antigos."""

from app.modules.clients.adapters.http.dependencies import ClientsUnitOfWorkDep

__all__ = ["ClientsUnitOfWorkDep"]
