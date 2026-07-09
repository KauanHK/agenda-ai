from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import settings


class _DataBase:
    def __init__(self) -> None:
        """Inicializa o banco de dados."""

        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def is_initialized(self) -> bool:
        """Verifica se o banco de dados foi inicializado."""

        return self._engine is not None and self._session_factory is not None

    def init(self) -> None:
        """
        Inicializa o engine do banco de dados e o sessionmaker,
        se ainda não estiverem inicializados.
        """

        if self.is_initialized():
            return

        self._engine = create_async_engine(
            settings.sqlalchemy_database_uri,
            pool_pre_ping=True,
            future=True,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    async def close(self) -> None:
        """Fecha a conexão com o banco de dados."""

        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    def create_session(self) -> AsyncSession:
        """
        Cria e retorna uma nova sessão assíncrona do SQLAlchemy.
        Returns:
            AsyncSession:
                Uma nova sessão assíncrona do SQLAlchemy.
        """

        if self._session_factory is None:
            raise RuntimeError("Database engine not initialized.")
        return self._session_factory()

    async def session_context(self) -> AsyncGenerator[AsyncSession]:
        """
        Cria e fornece uma sessão assíncrona do SQLAlchemy.

        Yields:
            AsyncSession:
                Uma sessão assíncrona do SQLAlchemy para interagir com o banco de dados.
        """

        async with self.create_session() as session:
            yield session


db = _DataBase()
