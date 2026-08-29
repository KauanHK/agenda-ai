"""Compat: o `ClientsDeleter` agora vive em
`app.modules.clients.application.use_cases.delete`. Re-export para imports antigos."""

from app.modules.clients.application.use_cases.delete import ClientsDeleter

__all__ = ["ClientsDeleter"]
