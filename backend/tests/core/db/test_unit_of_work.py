import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.db.unit_of_work import BaseUnitOfWork


def make_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


def make_uow(session: AsyncMock | None = None) -> tuple[BaseUnitOfWork, AsyncMock]:
    if session is None:
        session = make_session()
    factory = MagicMock(return_value=session)
    uow = BaseUnitOfWork(session_factory=factory)
    return uow, session


class TestInit:
    def test_stores_session_factory(self):
        factory = MagicMock()
        uow = BaseUnitOfWork(session_factory=factory)

        assert uow._session_factory is factory

    def test_session_is_initially_none(self):
        uow = BaseUnitOfWork(session_factory=MagicMock())

        assert uow._session is None


class TestSessionProperty:
    def test_raises_when_session_not_initialized(self):
        uow = BaseUnitOfWork(session_factory=MagicMock())

        with pytest.raises(RuntimeError, match="não inicializada"):
            _ = uow.session

    async def test_returns_session_after_enter(self):
        uow, session = make_uow()

        async with uow:
            assert uow.session is session


class TestAenter:
    async def test_calls_session_factory(self):
        session = make_session()
        factory = MagicMock(return_value=session)
        uow = BaseUnitOfWork(session_factory=factory)

        async with uow:
            pass

        factory.assert_called_once()

    async def test_returns_self(self):
        uow, _ = make_uow()

        result = await uow.__aenter__()

        assert result is uow
        await uow.__aexit__(None, None, None)


class TestAexit:
    async def test_commits_when_no_exception(self):
        uow, session = make_uow()

        async with uow:
            pass

        session.commit.assert_awaited_once()

    async def test_closes_session_after_commit(self):
        uow, session = make_uow()

        async with uow:
            pass

        session.close.assert_awaited_once()

    async def test_rolls_back_on_exception(self):
        uow, session = make_uow()

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("erro")

        session.rollback.assert_awaited_once()

    async def test_does_not_commit_on_exception(self):
        uow, session = make_uow()

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("erro")

        session.commit.assert_not_awaited()

    async def test_closes_session_after_rollback(self):
        uow, session = make_uow()

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("erro")

        session.close.assert_awaited_once()

    async def test_closes_session_even_when_commit_fails(self):
        uow, session = make_uow()
        session.commit.side_effect = RuntimeError("db error")

        with pytest.raises(RuntimeError):
            async with uow:
                pass

        session.close.assert_awaited_once()

    async def test_does_not_suppress_exception(self):
        uow, _ = make_uow()

        with pytest.raises(RuntimeError, match="boom"):
            async with uow:
                raise RuntimeError("boom")


class TestHandleCommit:
    async def test_commits_session(self):
        uow, session = make_uow()
        await uow.__aenter__()

        await uow._handle_commit()

        session.commit.assert_awaited_once()

    async def test_reraises_on_commit_failure(self):
        uow, session = make_uow()
        session.commit.side_effect = RuntimeError("db error")
        await uow.__aenter__()

        with pytest.raises(RuntimeError, match="db error"):
            await uow._handle_commit()

    async def test_rolls_back_on_commit_failure(self):
        uow, session = make_uow()
        session.commit.side_effect = RuntimeError("db error")
        await uow.__aenter__()

        with pytest.raises(RuntimeError):
            await uow._handle_commit()

        session.rollback.assert_awaited_once()

    async def test_logs_error_on_commit_failure(self, caplog: pytest.LogCaptureFixture):
        uow, session = make_uow()
        session.commit.side_effect = RuntimeError("db error")
        await uow.__aenter__()

        with (
            caplog.at_level(logging.ERROR, logger="app.core.db.unit_of_work"),
            pytest.raises(RuntimeError),
        ):
            await uow._handle_commit()

        assert "commit" in caplog.text.lower()


class TestHandleRollback:
    async def test_rolls_back_session(self):
        uow, session = make_uow()
        await uow.__aenter__()

        await uow._handle_rollback()

        session.rollback.assert_awaited_once()

    async def test_does_not_reraise_on_rollback_failure(self):
        uow, session = make_uow()
        session.rollback.side_effect = Exception("rollback error")
        await uow.__aenter__()

        await uow._handle_rollback()  # não deve levantar

    async def test_logs_error_on_rollback_failure(
        self, caplog: pytest.LogCaptureFixture
    ):
        uow, session = make_uow()
        session.rollback.side_effect = Exception("rollback error")
        await uow.__aenter__()

        with caplog.at_level(logging.ERROR, logger="app.core.db.unit_of_work"):
            await uow._handle_rollback()

        assert "rollback" in caplog.text.lower()
