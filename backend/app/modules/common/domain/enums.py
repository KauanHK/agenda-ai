"""Compat: `DocumentType` agora vive em `app.modules.establishments.domain.enums`.
Re-export para imports antigos."""

from app.modules.establishments.domain.enums import DocumentType

__all__ = ["DocumentType"]
