"""Compat: o repositório agora vive em
`app.modules.clients.adapters.db.repository`. Re-export para imports antigos
(consumido por app.modules.schedulings, app.modules.agent e pelo worker Celery)."""

from app.modules.clients.adapters.db.repository import ClientsRepository

__all__ = ["ClientsRepository"]
