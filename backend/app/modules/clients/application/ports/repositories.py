from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.domain.entities import Client, NewClient, UpdateClient


class ClientsRepositoryProtocol(
    BaseRepositoryProtocol[Client, ClientFilters, NewClient, UpdateClient],
    Protocol,
): ...
