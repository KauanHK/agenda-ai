"""
Compat: o singleton de banco agora vive em `app.core.db.session`. Re-export para
imports antigos. O import de `app.db.models` preserva o efeito colateral original de
registrar todos os models no metadata da `Base`.
"""

import app.db.models  # noqa: F401
from app.core.db.session import _DataBase as DataBase
from app.core.db.session import db

__all__ = ["DataBase", "db"]
