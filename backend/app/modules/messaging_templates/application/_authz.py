"""Compat: as regras de autorização agora vivem em
`app.modules.messaging_templates.application.authz`. Re-export para imports antigos."""

from app.modules.messaging_templates.application.authz import (
    assert_can_access,
    assert_can_write,
)

__all__ = ["assert_can_access", "assert_can_write"]
