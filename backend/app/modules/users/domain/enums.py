"""Compat: `UserRole` agora vive em `app.core.roles`. Re-export para imports antigos."""

from app.core.roles import UserRole

__all__ = ["UserRole"]
