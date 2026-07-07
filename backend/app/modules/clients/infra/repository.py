import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.clients.domain.filters import ClientFilters
from app.modules.clients.domain.model import Client


class ClientsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id_or_none(
        self,
        client_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Client | None:
        """Retorna o cliente com o id informado ou None caso não exista."""
        client = await self._session.get(Client, client_id)
        if not include_deleted and client is not None and client.deleted_at is not None:
            return None
        return client

    async def get_by_id(
        self,
        client_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Client:
        """Retorna o cliente com o id informado, levantando NotFoundError se ausente."""
        client = await self.get_by_id_or_none(client_id, include_deleted=include_deleted)
        if client is None:
            raise NotFoundError("Client not found.")
        return client

    async def create(self, client: Client) -> Client:
        """Persiste um novo cliente e o retorna já com os campos atualizados."""
        self._session.add(client)
        await self._session.flush()
        await self._session.refresh(client)
        return client

    async def update(self, client: Client) -> Client:
        """Atualiza um cliente existente e retorna a instância gerenciada."""
        merged = await self._session.merge(client)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def list(
        self,
        pagination: PaginationParams,
        filters: ClientFilters | None = None,
        include_deleted: bool = False,
    ) -> list[Client]:
        """Lista clientes aplicando filtros e paginação."""
        query = self._construct_select_query(filters, include_deleted=include_deleted)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(
        self,
        filters: ClientFilters | None = None,
        include_deleted: bool = False,
    ) -> int:
        """Retorna a quantidade total de clientes que satisfazem os filtros."""
        query = select(func.count()).select_from(  # pylint: disable=not-callable
            self._construct_select_query(filters, include_deleted=include_deleted).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    def _construct_select_query(
        self,
        filters: ClientFilters | None = None,
        include_deleted: bool = False,
    ) -> Select[tuple[Client]]:
        query = select(Client)
        if not include_deleted:
            query = query.where(Client.deleted_at.is_(None))
        if filters is None:
            return query
        if filters.establishment_id is not None:
            query = query.where(Client.establishment_id == filters.establishment_id)
        if filters.is_active is not None:
            query = query.where(Client.is_active == filters.is_active)
        if filters.q is not None:
            like = f"%{filters.q}%"
            query = query.where(
                or_(
                    Client.name.ilike(like),
                    Client.phone.ilike(like),
                    Client.email.ilike(like),
                )
            )
        return query
