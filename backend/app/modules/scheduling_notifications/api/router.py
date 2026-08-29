"""Compat: o router agora vive em
`app.modules.scheduling_notifications.adapters.http.router`. Re-export para imports
antigos (consumido por app.api.router, a composition root)."""

from app.modules.scheduling_notifications.adapters.http.router import router

__all__ = ["router"]
