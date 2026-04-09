# -*- coding: utf-8 -*-
"""Codex-oriented integration exports for Agent Reach."""

from __future__ import annotations

import os
from pathlib import Path

from agent_reach.channels import get_all_channel_contracts
from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp

EXA_SERVER_URL = "https://mcp.exa.ai/mcp"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_skill_roots() -> list[Path]:
    roots: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        roots.append(Path(codex_home) / "skills")
    roots.append(Path.home() / ".codex" / "skills")
    roots.append(Path.home() / ".agents" / "skills")
    return roots


def _required_commands(channels: list[dict]) -> list[str]:
    commands = set()
    for channel in channels:
        commands.update(channel.get("required_commands", []))
    return sorted(commands)


def _mcp_snippet() -> dict:
    return {
        "mcpServers": {
            "exa": {
                "type": "http",
                "url": EXA_SERVER_URL,
            }
        }
    }


def export_codex_integration() -> dict:
    """Return the stable integration payload for Codex on Windows."""

    repo_root = _repo_root()
    channels = get_all_channel_contracts()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "client": "codex",
        "platform": "windows",
        "positioning": [
            "bootstrapper",
            "channel_registry",
            "readiness_layer",
            "integration_helper",
        ],
        "channels": channels,
        "required_commands": _required_commands(channels),
        "skill": {
            "source": str(repo_root / "agent_reach" / "skill"),
            "targets": [str(root / "agent-reach") for root in _candidate_skill_roots()],
        },
        "plugin_manifest": str(repo_root / ".codex-plugin" / "plugin.json"),
        "mcp_config": str(repo_root / ".mcp.json"),
        "mcp_snippet": _mcp_snippet(),
        "verification_commands": [
            "agent-reach channels --json",
            "agent-reach doctor --json",
            "agent-reach doctor --json --probe",
            'agent-reach collect --channel github --operation read --input "openai/openai-python" --json',
            'agent-reach collect --channel web --operation read --input "https://example.com" --json',
            "agent-reach export-integration --client codex --format json",
        ],
        "python_sdk": {
            "import": "from agent_reach import AgentReachClient",
            "quickstart": [
                "client = AgentReachClient()",
                'client.github.read("openai/openai-python")',
            ],
        },
        "recommended_docs": [
            str(repo_root / "docs" / "codex-integration.md"),
            str(repo_root / "docs" / "codex-compatibility.md"),
            str(repo_root / "docs" / "python-sdk.md"),
        ],
    }


def render_codex_integration_text(payload: dict) -> str:
    """Render a human-readable integration summary."""

    lines = [
        "Agent Reach integration export for Codex on Windows",
        "========================================",
        "",
        "Positioning:",
        "  bootstrapper, channel registry, readiness layer, integration helper",
        "",
        f"Plugin manifest: {payload['plugin_manifest']}",
        f"MCP config: {payload['mcp_config']}",
        f"Skill source: {payload['skill']['source']}",
        "Skill targets:",
    ]
    for target in payload["skill"]["targets"]:
        lines.append(f"  {target}")
    lines.extend(
        [
            "",
            "Required commands:",
        ]
    )
    for command in payload["required_commands"]:
        lines.append(f"  {command}")
    lines.extend(
        [
            "",
            "Verification commands:",
        ]
    )
    for command in payload["verification_commands"]:
        lines.append(f"  {command}")
    return "\n".join(lines)


def render_codex_integration_powershell(payload: dict) -> str:
    """Render a PowerShell-oriented export snippet."""

    skill_targets = ",\n".join(f'  "{target}"' for target in payload["skill"]["targets"])
    return "\n".join(
        [
            "# Agent Reach integration export for Codex on Windows",
            f'$pluginManifest = "{payload["plugin_manifest"]}"',
            f'$mcpConfig = "{payload["mcp_config"]}"',
            f'$skillSource = "{payload["skill"]["source"]}"',
            "$skillTargets = @(",
            skill_targets,
            ")",
            "",
            "# MCP snippet",
            "@'",
            "{",
            '  "mcpServers": {',
            '    "exa": {',
            '      "type": "http",',
            f'      "url": "{payload["mcp_snippet"]["mcpServers"]["exa"]["url"]}"',
            "    }",
            "  }",
            "}",
            "'@",
            "",
            "# Verification commands",
            "agent-reach channels --json",
            "agent-reach doctor --json",
            "agent-reach doctor --json --probe",
            'agent-reach collect --channel github --operation read --input "openai/openai-python" --json',
        ]
    )
