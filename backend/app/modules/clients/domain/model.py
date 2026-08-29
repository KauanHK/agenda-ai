"""Compat: o model SQLAlchemy agora vive em
`app.modules.clients.adapters.db.models`. Re-export para imports antigos (consumido
por app.db.models, app.modules.schedulings, app.modules.agent e pelo worker Celery)."""

from app.modules.clients.adapters.db.models import Client

__all__ = ["Client"]
