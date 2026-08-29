"""Compat: o `ClientsCreator` agora vive em
`app.modules.clients.application.use_cases.create`. Re-export para imports antigos."""

from app.modules.clients.application.use_cases.create import ClientsCreator

__all__ = ["ClientsCreator"]
