"""Compat: o model SQLAlchemy agora vive em
`app.modules.unavailabilities.adapters.db.models`. Re-export para imports antigos
(consumido por app.db.models, o registry que o Alembic usa para gerar as migrations)."""

from app.modules.unavailabilities.adapters.db.models import Unavailability

__all__ = ["Unavailability"]
