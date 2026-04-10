# -*- coding: utf-8 -*-
"""Tests for repo-shipped integration artifacts."""

import json
from pathlib import Path
from unittest.mock import patch

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


def test_export_points_at_existing_checkout_artifacts():
    payload = export_codex_integration()

    assert payload["client"] == "codex"
    assert payload["execution_context"] == "checkout"
    assert payload["plugin_manifest"] is not None
    assert payload["mcp_config"] is not None
    assert Path(payload["plugin_manifest"]).exists()
    assert Path(payload["mcp_config"]).exists()
    assert all(Path(path).exists() for path in payload["recommended_docs"])
    assert payload["skill"]["targets"]
    assert Path(payload["skill"]["source"]).exists()
    assert payload["python_sdk"]["availability"] == "project_env_only"
    assert payload["python_sdk"]["import"] == "from agent_reach import AgentReachClient"
    assert any(command.startswith("agent-reach collect ") for command in payload["verification_commands"])


def test_export_tool_install_omits_dead_paths(tmp_path):
    fake_repo_root = tmp_path / "site-packages"
    fake_repo_root.mkdir(parents=True)

    with patch("agent_reach.integrations.codex._repo_root", return_value=fake_repo_root), patch(
        "agent_reach.integrations.codex._current_working_dir",
        return_value=tmp_path / "consumer-project",
    ):
        payload = export_codex_integration()

    assert payload["execution_context"] == "tool_install"
    assert payload["plugin_manifest"] is None
    assert payload["mcp_config"] is None
    assert payload["recommended_docs"] == []
    assert payload["plugin_manifest_inline"]["name"] == "agent-reach"
    assert payload["plugin_manifest_inline"]["skills"] == payload["skill"]["source"]
    assert payload["plugin_manifest_inline"]["mcpServers"] == "../.mcp.json"
    assert payload["mcp_config_inline"]["mcpServers"]["exa"]["url"] == "https://mcp.exa.ai/mcp"
    assert payload["suggested_destinations"]["plugin_manifest"].endswith(".codex-plugin\\plugin.json")
    assert payload["suggested_destinations"]["mcp_config"].endswith(".mcp.json")
    assert payload["documentation_summary"]
    assert payload["inline_payload_notes"]
