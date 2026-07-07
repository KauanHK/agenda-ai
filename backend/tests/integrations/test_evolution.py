from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.integrations.evolution import EvolutionAPIError, send_text


def _mock_settings():
    s = MagicMock()
    s.EVOLUTION_URL = "http://evo"
    s.EVOLUTION_INSTANCE = "inst"
    s.EVOLUTION_APIKEY = "key"
    return s


def test_send_text_success():
    mock_response = MagicMock()
    mock_response.is_success = True
    with (
        patch("app.integrations.evolution.settings", _mock_settings()),
        patch("app.integrations.evolution.httpx.Client") as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        send_text("5548999999999", "Olá mundo")
        mock_client.return_value.__enter__.return_value.post.assert_called_once_with(
            "http://evo/message/sendText/inst",
            json={"number": "5548999999999", "text": "Olá mundo"},
            headers={"apikey": "key"},
        )


def test_send_text_raises_on_non_2xx():
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    with (
        patch("app.integrations.evolution.settings", _mock_settings()),
        patch("app.integrations.evolution.httpx.Client") as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        with pytest.raises(EvolutionAPIError) as exc_info:
            send_text("5548999999999", "Olá mundo")
        assert exc_info.value.status_code == 500
        assert "500" in str(exc_info.value)


def test_send_text_raises_on_transport_error():
    with (
        patch("app.integrations.evolution.settings", _mock_settings()),
        patch("app.integrations.evolution.httpx.Client") as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.post.side_effect = httpx.ConnectError("refused")
        with pytest.raises(EvolutionAPIError) as exc_info:
            send_text("5548999999999", "Olá mundo")
        assert exc_info.value.status_code == 0
