"""Compat: o router agora vive em
`app.modules.messaging_templates.adapters.http.router`. Re-export para imports
antigos (consumido por app.api.router, a composition root)."""

from app.modules.messaging_templates.adapters.http.router import router

__all__ = ["router"]
