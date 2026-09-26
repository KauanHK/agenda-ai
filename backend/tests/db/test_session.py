from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.session import DataBase

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/testdb"


@pytest.fixture
def database() -> DataBase:
    return DataBase()


@pytest.fixture
def initialized_database(database: DataBase) -> DataBase:
    with (
        patch("app.core.db.session.create_async_engine") as mock_engine,
        patch("app.core.db.session.async_sessionmaker") as mock_sessionmaker,
    ):
        mock_engine.return_value = MagicMock()
        mock_sessionmaker.return_value = MagicMock()
        database.init()
    return database


def test_init_state_is_none(database: DataBase):
    assert database._engine is None
    assert database._session_factory is None


def test_init_creates_engine_and_session_factory(database: DataBase):

    with (
        patch("app.core.db.session.create_async_engine") as mock_engine,
        patch("app.core.db.session.async_sessionmaker") as mock_sessionmaker,
        patch("app.core.db.session.settings") as mock_settings,
    ):
        mock_settings.sqlalchemy_database_uri = DATABASE_URL
        mock_engine.return_value = MagicMock()
        mock_sessionmaker.return_value = MagicMock()

        database.init()

        mock_engine.assert_called_once_with(
            DATABASE_URL,
            pool_pre_ping=True,
            future=True,
        )
        mock_sessionmaker.assert_called_once()
        assert database._engine is not None
        assert database._session_factory is not None


def test_init_is_idempotent(database: DataBase):
    """Segunda chamada ao init() não deve recriar engine e session_factory."""

    with (
        patch("app.core.db.session.create_async_engine") as mock_engine,
        patch("app.core.db.session.async_sessionmaker") as mock_sessionmaker,
        patch("app.core.db.session.settings") as mock_settings,
    ):
        mock_settings.sqlalchemy_database_uri = DATABASE_URL
        mock_engine.return_value = MagicMock()
        mock_sessionmaker.return_value = MagicMock()

        database.init()
        database.init()

        mock_engine.assert_called_once()
        mock_sessionmaker.assert_called_once()


async def test_close_disposes_engine(initialized_database: DataBase):
    mock_engine = initialized_database._engine
    mock_engine.dispose = AsyncMock()

    await initialized_database.close()

    mock_engine.dispose.assert_awaited_once()


async def test_close_resets_state(initialized_database: DataBase):
    initialized_database._engine.dispose = AsyncMock()

    await initialized_database.close()

    assert initialized_database._engine is None
    assert initialized_database._session_factory is None


async def test_close_when_not_initialized_does_nothing(database: DataBase):
    """close() sem init() anterior não deve levantar exceção."""
    await database.close()

    assert database._engine is None
    assert database._session_factory is None


async def test_close_allows_reinit(initialized_database: DataBase):
    """Após close(), init() deve poder ser chamado novamente."""
    initialized_database._engine.dispose = AsyncMock()
    await initialized_database.close()

    with (
        patch("app.core.db.session.create_async_engine") as mock_engine,
        patch("app.core.db.session.async_sessionmaker") as mock_sessionmaker,
        patch("app.core.db.session.settings") as mock_settings,
    ):
        mock_settings.sqlalchemy_database_uri = DATABASE_URL
        mock_engine.return_value = MagicMock()
        mock_sessionmaker.return_value = MagicMock()

        initialized_database.init()

        mock_engine.assert_called_once()
        assert initialized_database._engine is not None


async def test_get_session_raises_if_not_initialized(database: DataBase):
    with pytest.raises(RuntimeError, match=r"Database engine not initialized\."):
        async for _ in database.session_context():
            pass


async def test_get_session_yields_session(database: DataBase):
    mock_session = MagicMock(spec=AsyncMock)
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(return_value=mock_context)

    database._engine = MagicMock()
    database._session_factory = mock_factory

    async for session in database.session_context():
        assert session is mock_session
