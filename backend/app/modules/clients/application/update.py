"""Compat: o `ClientsUpdater` agora vive em
`app.modules.clients.application.use_cases.update`. Re-export para imports antigos."""

from app.modules.clients.application.use_cases.update import ClientsUpdater

__all__ = ["ClientsUpdater"]
