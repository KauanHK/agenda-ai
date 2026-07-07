import uuid
from unittest.mock import AsyncMock, MagicMock

from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.infra.repository import MessagingTemplatesRepository


async def test_get_active_templates_for_service_returns_matching():
    service_id = uuid.uuid7()
    establishment_id = uuid.uuid7()
    template = MagicMock(spec=MessagingTemplate)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = [template]
    mock_session.execute.return_value = mock_result

    repo = MessagingTemplatesRepository(mock_session)
    result = await repo.get_active_templates_for_service(service_id, establishment_id)

    assert result == [template]
    mock_session.execute.assert_called_once()


async def test_get_active_templates_for_service_returns_empty_when_none():
    service_id = uuid.uuid7()
    establishment_id = uuid.uuid7()

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = []
    mock_session.execute.return_value = mock_result

    repo = MessagingTemplatesRepository(mock_session)
    result = await repo.get_active_templates_for_service(service_id, establishment_id)

    assert result == []


async def test_get_active_templates_for_service_query_has_required_predicates():
    service_id = uuid.uuid7()
    establishment_id = uuid.uuid7()

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = []
    mock_session.execute.return_value = mock_result

    repo = MessagingTemplatesRepository(mock_session)
    await repo.get_active_templates_for_service(service_id, establishment_id)

    query = mock_session.execute.call_args[0][0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "is_active" in compiled
    assert "deleted_at" in compiled
    assert "minutes_before" in compiled
