"""Testes do logging estruturado: linha JSON, `thread_id` e nível."""

import io
import json
import logging

import httpx
import pytest

from src.logging_config import (
    JsonFormatter,
    _ThreadIdFilter,
    bind_thread_id,
    configure_logging,
)


def _capture() -> tuple[logging.Logger, io.StringIO]:
    """Um logger isolado com o handler JSON e o filtro de `thread_id`."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(_ThreadIdFilter())

    logger = logging.getLogger("tests.logging_config")
    logger.handlers[:] = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger, stream


def test_cada_registro_e_uma_linha_json_valida() -> None:
    logger, stream = _capture()

    logger.info("olá mundo")

    line = stream.getvalue().strip()
    assert "\n" not in line
    record = json.loads(line)
    assert record["msg"] == "olá mundo"
    assert record["level"] == "INFO"
    assert record["logger"] == "tests.logging_config"
    assert record["ts"].endswith("+00:00")


def test_thread_id_presente_com_o_contextvar_setado() -> None:
    logger, stream = _capture()

    with bind_thread_id("telegram:42"):
        logger.info("dentro do turno")

    assert json.loads(stream.getvalue())["thread_id"] == "telegram:42"


def test_thread_id_ausente_sem_o_contextvar() -> None:
    logger, stream = _capture()

    logger.info("fora de qualquer turno")

    assert "thread_id" not in json.loads(stream.getvalue())


def test_bind_thread_id_e_restaurado_ao_sair_do_bloco() -> None:
    logger, stream = _capture()

    with bind_thread_id("telegram:1"):
        pass
    logger.info("depois do bloco")

    assert "thread_id" not in json.loads(stream.getvalue())


def test_campos_extra_entram_no_json() -> None:
    logger, stream = _capture()

    logger.info("com extra", extra={"establishment_id": "abc-123"})

    assert json.loads(stream.getvalue())["establishment_id"] == "abc-123"


def test_exc_info_vira_texto_no_json() -> None:
    logger, stream = _capture()

    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("deu ruim")

    record = json.loads(stream.getvalue())
    assert "ValueError: boom" in record["exc_info"]


def test_configure_logging_respeita_o_nivel() -> None:
    configure_logging("WARNING")
    root = logging.getLogger()

    assert root.level == logging.WARNING
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)


def test_configure_logging_e_idempotente() -> None:
    configure_logging("INFO")
    configure_logging("DEBUG")

    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == logging.DEBUG


def test_configure_logging_nao_loga_a_url_com_o_token_do_bot(
    caplog: pytest.LogCaptureFixture,
) -> None:
    configure_logging("DEBUG")
    # `force=True` tirou o handler do caplog do root; recoloca.
    logging.getLogger().addHandler(caplog.handler)

    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True}))
    with httpx.Client(transport=transport) as client:
        client.post("https://api.telegram.org/bot123:SECRET/sendMessage")
    logging.getLogger("src.app").info("log da aplicação")

    assert not any("SECRET" in record.getMessage() for record in caplog.records)
    assert any(record.getMessage() == "log da aplicação" for record in caplog.records)
