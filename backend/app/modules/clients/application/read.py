"""Compat: os use cases de leitura agora vivem em
`app.modules.clients.application.use_cases`. Re-export para imports antigos."""

from app.modules.clients.application.use_cases.paginator import ClientsPaginator
from app.modules.clients.application.use_cases.read import ClientsReader

__all__ = ["ClientsPaginator", "ClientsReader"]
