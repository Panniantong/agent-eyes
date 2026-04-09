# -*- coding: utf-8 -*-
"""Tests for repo-shipped integration artifacts."""

import json
from pathlib import Path

from agent_reach.integrations.codex import export_codex_integration


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_codex_plugin_manifest_exists_and_is_valid():
    manifest_path = _repo_root() / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["name"] == "agent-reach"
    assert manifest["skills"] == "../agent_reach/skill"
    assert manifest["mcpServers"] == "../.mcp.json"
    assert manifest["interface"]["displayName"] == "Agent Reach"
    assert "Collection" in manifest["interface"]["capabilities"]


def test_mcp_config_contains_exa():
    mcp_path = _repo_root() / ".mcp.json"
    payload = json.loads(mcp_path.read_text(encoding="utf-8"))

    assert payload["mcpServers"]["exa"]["url"] == "https://mcp.exa.ai/mcp"


def test_export_points_at_repo_artifacts():
    payload = export_codex_integration()

    assert payload["client"] == "codex"
    assert Path(payload["plugin_manifest"]).name == "plugin.json"
    assert Path(payload["mcp_config"]).name == ".mcp.json"
    assert payload["skill"]["targets"]
    assert payload["python_sdk"]["import"] == "from agent_reach import AgentReachClient"
    assert any(command.startswith("agent-reach collect ") for command in payload["verification_commands"])
