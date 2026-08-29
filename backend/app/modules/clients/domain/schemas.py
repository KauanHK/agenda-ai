"""Compat: os schemas HTTP agora vivem em
`app.modules.clients.adapters.http.schemas`. Re-export para imports antigos."""

from app.modules.clients.adapters.http.schemas import (
    ClientBase,
    ClientCreate,
    ClientRead,
    ClientUpdate,
    Name,
    Phone,
)

__all__ = [
    "ClientBase",
    "ClientCreate",
    "ClientRead",
    "ClientUpdate",
    "Name",
    "Phone",
]
