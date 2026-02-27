# -*- coding: utf-8 -*-
"""Tests for local telemetry helpers."""

import json

from agent_reach.config import Config
from agent_reach.telemetry import record_cli_event, telemetry_enabled, telemetry_path


def test_telemetry_env_override_off(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_REACH_TELEMETRY", "0")
    cfg = Config(config_path=tmp_path / "config.yaml")
    assert telemetry_enabled(cfg) is False


def test_telemetry_records_local_event(tmp_path):
    cfg = Config(config_path=tmp_path / "config.yaml")
    record_cli_event(
        command="doctor",
        status="ok",
        duration_ms=42,
        config=cfg,
        details={"result": "up_to_date"},
    )

    path = telemetry_path(cfg)
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8").strip())
    assert payload["event"] == "cli_command"
    assert payload["command"] == "doctor"
    assert payload["status"] == "ok"
    assert payload["duration_ms"] == 42
