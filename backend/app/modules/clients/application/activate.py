"""Compat: o `ClientsActivator` agora vive em
`app.modules.clients.application.use_cases.activate`. Re-export para imports antigos."""

from app.modules.clients.application.use_cases.activate import ClientsActivator

__all__ = ["ClientsActivator"]
