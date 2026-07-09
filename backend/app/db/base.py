"""Compat: a `Base` agora vive em `app.core.db.base`. Re-export para imports antigos."""

from app.core.db.base import Base

__all__ = ["Base"]
