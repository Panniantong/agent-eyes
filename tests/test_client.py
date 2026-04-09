# -*- coding: utf-8 -*-
"""Tests for the external Agent Reach SDK surface."""

from agent_reach.client import AgentReach, AgentReachClient
from agent_reach.config import Config
from agent_reach.results import build_result


class _StubAdapter:
    channel = "github"

    def __init__(self, config=None):
        self.config = config

    def supported_operations(self):
        return ("read",)

    def read(self, value, limit=None):
        return build_result(
            ok=True,
            channel="github",
            operation="read",
            items=[
                {
                    "id": value,
                    "kind": "repository",
                    "title": value,
                    "url": f"https://github.com/{value}",
                    "text": None,
                    "author": "openai",
                    "published_at": None,
                    "source": "github",
                    "extras": {},
                }
            ],
            raw={"value": value, "limit": limit},
            meta={"input": value},
            error=None,
        )


def test_agent_reach_alias_and_namespace_access(tmp_path, monkeypatch):
    config = Config(config_path=tmp_path / "config.yaml")
    monkeypatch.setattr("agent_reach.client.get_adapter", lambda channel, config=None: _StubAdapter(config=config))

    client = AgentReachClient(config=config)
    legacy = AgentReach(config=config)

    assert client.exa_search is client.exa
    assert isinstance(legacy, AgentReachClient)
    assert client.github.read("openai/openai-python")["ok"] is True


def test_collect_rejects_blank_input(tmp_path):
    client = AgentReachClient(config=Config(config_path=tmp_path / "config.yaml"))

    payload = client.collect("github", "read", "   ")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_input"


def test_collect_rejects_invalid_limit(tmp_path):
    client = AgentReachClient(config=Config(config_path=tmp_path / "config.yaml"))

    payload = client.collect("github", "read", "openai/openai-python", limit=0)

    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_input"


def test_collect_reports_unsupported_operation(tmp_path, monkeypatch):
    config = Config(config_path=tmp_path / "config.yaml")
    monkeypatch.setattr("agent_reach.client.get_adapter", lambda channel, config=None: _StubAdapter(config=config))
    client = AgentReachClient(config=config)

    payload = client.collect("github", "search", "openai")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "unsupported_operation"
    assert payload["meta"]["supported_operations"] == ["read"]


def test_collect_reports_unknown_channel(tmp_path, monkeypatch):
    config = Config(config_path=tmp_path / "config.yaml")
    monkeypatch.setattr("agent_reach.client.get_adapter", lambda channel, config=None: None)
    client = AgentReachClient(config=config)

    payload = client.collect("missing", "read", "value")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "unknown_channel"


def test_collect_catches_unexpected_adapter_error(tmp_path, monkeypatch):
    class _BoomAdapter:
        def supported_operations(self):
            return ("read",)

        def read(self, value):
            raise RuntimeError("boom")

    config = Config(config_path=tmp_path / "config.yaml")
    monkeypatch.setattr("agent_reach.client.get_adapter", lambda channel, config=None: _BoomAdapter())
    client = AgentReachClient(config=config)

    payload = client.collect("github", "read", "openai/openai-python")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "internal_error"
