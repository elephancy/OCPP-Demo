from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import structlog
from app.core import logging as app_logging
from app.core import observability


def test_injected_log_level_filters_semantic_events(monkeypatch, capsys):
    monkeypatch.setenv("LOG_LEVEL", "error")
    app_logging.configure_logging()
    logger = structlog.get_logger()
    logger.info("request_finished", request_id="request-1", status_code=200)
    logger.error("delivery_failed", request_id="request-2", retryable=True)

    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(records) == 1
    assert records[0]["event"] == "delivery_failed"
    assert records[0]["level"] == "error"
    assert records[0]["request_id"] == "request-2"
    assert records[0]["retryable"] is True


def test_unconfigured_local_logging_uses_python_warning_threshold(monkeypatch, capsys):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    app_logging.configure_logging()
    logger = structlog.get_logger()
    logger.info("routine_event")
    logger.warning("operator_attention")

    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [record["event"] for record in records] == ["operator_attention"]


def test_invalid_log_level_fails_explicitly(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        app_logging.configure_logging()


def test_unconfigured_tracing_does_not_start_exporter(monkeypatch):
    monkeypatch.setattr(observability, "get_settings", lambda: SimpleNamespace(
        app_env="development", otel_exporter_otlp_endpoint=None,
    ))

    def unexpected_exporter(**kwargs):
        pytest.fail("An unconfigured local run must not start a network exporter")

    monkeypatch.setattr(observability, "OTLPSpanExporter", unexpected_exporter)
    observability.configure_tracing()


def test_injected_tracing_endpoint_is_used_without_duplicate_slash(monkeypatch):
    monkeypatch.setattr(observability, "get_settings", lambda: SimpleNamespace(
        app_env="production", app_name="charging-api", app_version="test-version",
        otel_exporter_otlp_endpoint="http://central-collector:4318/",
    ))
    endpoints = []
    provider = SimpleNamespace(add_span_processor=lambda processor: None)
    monkeypatch.setattr(observability, "TracerProvider", lambda **kwargs: provider)
    monkeypatch.setattr(observability, "OTLPSpanExporter", lambda **kwargs: endpoints.append(kwargs["endpoint"]))
    monkeypatch.setattr(observability, "BatchSpanProcessor", lambda exporter: exporter)
    installed = []
    monkeypatch.setattr(observability.trace, "set_tracer_provider", installed.append)

    observability.configure_tracing()

    assert endpoints == ["http://central-collector:4318/v1/traces"]
    assert installed == [provider]
