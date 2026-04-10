# -*- coding: utf-8 -*-
"""Codex-oriented integration exports for Agent Reach."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from agent_reach import __version__
from agent_reach.channels import get_all_channel_contracts
from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp

EXA_SERVER_URL = "https://mcp.exa.ai/mcp"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _packaged_skill_source() -> Path:
    return Path(__file__).resolve().parents[1] / "skill"


def _current_working_dir() -> Path:
    return Path.cwd()


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


def _mcp_snippet() -> dict[str, Any]:
    return {
        "mcpServers": {
            "exa": {
                "type": "http",
                "url": EXA_SERVER_URL,
            }
        }
    }


def _artifact_paths(repo_root: Path) -> dict[str, Path]:
    return {
        "plugin_manifest": repo_root / ".codex-plugin" / "plugin.json",
        "mcp_config": repo_root / ".mcp.json",
        "docs_codex_integration": repo_root / "docs" / "codex-integration.md",
        "docs_codex_compatibility": repo_root / "docs" / "codex-compatibility.md",
        "docs_downstream_usage": repo_root / "docs" / "downstream-usage.md",
        "docs_python_sdk": repo_root / "docs" / "python-sdk.md",
    }


def _execution_context(repo_root: Path) -> str:
    paths = _artifact_paths(repo_root)
    if paths["plugin_manifest"].exists() and paths["mcp_config"].exists():
        return "checkout"
    return "tool_install"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _existing_path(path: Path) -> str | None:
    return str(path) if path.exists() else None


def _recommended_docs(repo_root: Path) -> list[str]:
    docs = [
        _artifact_paths(repo_root)["docs_codex_integration"],
        _artifact_paths(repo_root)["docs_codex_compatibility"],
        _artifact_paths(repo_root)["docs_downstream_usage"],
        _artifact_paths(repo_root)["docs_python_sdk"],
    ]
    return [str(path) for path in docs if path.exists()]


def _suggested_destinations(execution_context: str, repo_root: Path) -> dict[str, str]:
    base_dir = repo_root if execution_context == "checkout" else _current_working_dir()
    return {
        "plugin_manifest": str(base_dir / ".codex-plugin" / "plugin.json"),
        "mcp_config": str(base_dir / ".mcp.json"),
    }


def _default_plugin_manifest(skill_source: str, mcp_config_path: str) -> dict[str, Any]:
    return {
        "name": "agent-reach",
        "version": __version__,
        "description": "Windows-first research integration substrate for Codex and similar agents.",
        "author": {
            "name": "Neo Reid",
        },
        "license": "MIT",
        "keywords": [
            "codex",
            "windows",
            "research",
            "mcp",
            "diagnostics",
            "integration",
        ],
        "skills": skill_source,
        "mcpServers": mcp_config_path,
        "interface": {
            "displayName": "Agent Reach",
            "shortDescription": "Windows/Codex research integration substrate",
            "longDescription": (
                "Bootstraps, documents, diagnoses, and exposes thin read-only collection "
                "for downstream Codex workflows on Windows."
            ),
            "developerName": "Neo Reid",
            "category": "Developer Tools",
            "capabilities": [
                "Readiness",
                "Registry",
                "Collection",
            ],
            "defaultPrompt": [
                "Show me which research channels are ready on this Windows machine.",
                "Export the Codex integration settings for Agent Reach.",
                "List the supported channels and their setup requirements.",
                "Run a read-only collection for GitHub, web, RSS, Exa, Hatena Bookmark, Bluesky, Qiita, YouTube, or Twitter/X.",
            ],
            "brandColor": "#0F766E",
        },
    }


def _tool_install_plugin_mcp_reference() -> str:
    """Return the MCP reference expected after writing to the suggested Codex paths."""

    return "../.mcp.json"


def _plugin_manifest_inline(
    repo_root: Path,
    execution_context: str,
    skill_source: str,
) -> dict[str, Any]:
    payload = _read_json(_artifact_paths(repo_root)["plugin_manifest"])
    if payload is not None and execution_context == "checkout":
        return payload
    mcp_reference = (
        _tool_install_plugin_mcp_reference()
        if execution_context == "tool_install"
        else "../.mcp.json"
    )
    return _default_plugin_manifest(skill_source, mcp_reference)


def _mcp_config_inline(repo_root: Path) -> dict[str, Any]:
    payload = _read_json(_artifact_paths(repo_root)["mcp_config"])
    return payload if payload is not None else _mcp_snippet()


def _documentation_summary() -> list[str]:
    return [
        "Use `agent-reach collect --json` as the primary external interface in arbitrary projects.",
        "Use `agent-reach channels --json`, `doctor --json`, and `doctor --json --probe` for discovery and diagnostics.",
        "Tool installs expose the CLI. Import `AgentReachClient` only after installing Agent Reach into the caller Python environment.",
        "If `plugin_manifest` or `mcp_config` is null, write the inline payloads to the suggested destinations instead.",
    ]


def _inline_payload_notes() -> list[str]:
    return [
        "Write `plugin_manifest_inline` to `suggested_destinations.plugin_manifest` and `mcp_config_inline` to `suggested_destinations.mcp_config`.",
        "`plugin_manifest_inline.mcpServers` is a relative reference that resolves after both inline payloads are written to the suggested Codex paths.",
    ]


def _external_project_usage() -> dict[str, Any]:
    """Describe the no-copy downstream integration paths."""

    return {
        "copy_files_required": False,
        "preferred_interface": "agent-reach collect --json",
        "codex_global_install": {
            "commands": [
                "uv tool install --force git+https://github.com/iwachacha/Agent-Reach.git",
                "agent-reach skill --install",
                "agent-reach doctor --json --probe",
            ],
            "notes": [
                "The skill install writes to the user's Codex skill home, not to the downstream project.",
                "Downstream projects do not need `.codex-plugin`, `.mcp.json`, or `agent_reach/skill` files when using the CLI.",
            ],
        },
        "github_actions": {
            "uses": "iwachacha/Agent-Reach/.github/actions/setup-agent-reach@main",
            "notes": [
                "Use the composite action to install the CLI in the workflow without vendoring Agent Reach files.",
                "Pin `uses` to a tag or commit for reproducible automation.",
                "Keep scheduling, ranking, summarization, state, and Discord publishing in the downstream project.",
            ],
        },
        "discord_bot": {
            "recommended_pattern": "subprocess collector",
            "notes": [
                "Call `agent-reach collect --json` per source and map `items` into the bot's normalized item type.",
                "Treat Twitter/X as optional and gate it with `doctor --json --probe` when reliability matters.",
            ],
        },
    }


def export_codex_integration() -> dict[str, Any]:
    """Return the stable integration payload for Codex on Windows."""

    repo_root = _repo_root()
    execution_context = _execution_context(repo_root)
    artifact_paths = _artifact_paths(repo_root)
    channels = get_all_channel_contracts()
    skill_source = str(_packaged_skill_source())
    suggested_destinations = _suggested_destinations(execution_context, repo_root)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "client": "codex",
        "platform": "windows",
        "execution_context": execution_context,
        "positioning": [
            "bootstrapper",
            "channel_registry",
            "readiness_layer",
            "integration_helper",
        ],
        "channels": channels,
        "required_commands": _required_commands(channels),
        "skill": {
            "source": skill_source,
            "targets": [str(root / "agent-reach") for root in _candidate_skill_roots()],
        },
        "plugin_manifest": _existing_path(artifact_paths["plugin_manifest"]),
        "plugin_manifest_inline": _plugin_manifest_inline(
            repo_root,
            execution_context,
            skill_source,
        ),
        "mcp_config": _existing_path(artifact_paths["mcp_config"]),
        "mcp_config_inline": _mcp_config_inline(repo_root),
        "suggested_destinations": suggested_destinations,
        "inline_payload_notes": _inline_payload_notes(),
        "mcp_snippet": _mcp_snippet(),
        "external_project_usage": _external_project_usage(),
        "verification_commands": [
            "agent-reach channels --json",
            "agent-reach doctor --json",
            "agent-reach doctor --json --probe",
            'agent-reach collect --channel github --operation read --input "openai/openai-python" --json',
            'agent-reach collect --channel web --operation read --input "https://example.com" --json',
            "agent-reach export-integration --client codex --format json",
        ],
        "python_sdk": {
            "availability": "project_env_only",
            "import": "from agent_reach import AgentReachClient",
            "install_examples": [
                "uv pip install -e C:\\path\\to\\Agent-Reach",
                "uv pip install C:\\path\\to\\dist\\agent_reach-<version>-py3-none-any.whl",
            ],
            "quickstart": [
                "from agent_reach import AgentReachClient",
                "client = AgentReachClient()",
                'client.github.read("openai/openai-python")',
            ],
            "notes": [
                "uv tool install exposes the agent-reach CLI, not a general Python import in arbitrary projects.",
            ],
        },
        "recommended_docs": _recommended_docs(repo_root),
        "documentation_summary": _documentation_summary(),
    }


def render_codex_integration_text(payload: dict[str, Any]) -> str:
    """Render a human-readable integration summary."""

    lines = [
        "Agent Reach integration export for Codex on Windows",
        "========================================",
        "",
        f"Execution context: {payload['execution_context']}",
        "Positioning:",
        "  bootstrapper, channel registry, readiness layer, integration helper",
        "",
    ]
    if payload["plugin_manifest"]:
        lines.append(f"Plugin manifest: {payload['plugin_manifest']}")
    else:
        lines.append("Plugin manifest: not bundled in this tool install")
        lines.append(f"Suggested destination: {payload['suggested_destinations']['plugin_manifest']}")
    if payload["mcp_config"]:
        lines.append(f"MCP config: {payload['mcp_config']}")
    else:
        lines.append("MCP config: not bundled in this tool install")
        lines.append(f"Suggested destination: {payload['suggested_destinations']['mcp_config']}")
    lines.append(f"Skill source: {payload['skill']['source']}")
    lines.append("Skill targets:")
    for target in payload["skill"]["targets"]:
        lines.append(f"  {target}")

    if payload["recommended_docs"]:
        lines.extend(["", "Recommended docs:"])
        for path in payload["recommended_docs"]:
            lines.append(f"  {path}")
    else:
        lines.extend(["", "Documentation summary:"])
        for line in payload["documentation_summary"]:
            lines.append(f"  {line}")

    lines.extend(["", "Inline payload notes:"])
    for line in payload["inline_payload_notes"]:
        lines.append(f"  {line}")

    lines.extend(["", "Python SDK:"])
    lines.append(f"  availability: {payload['python_sdk']['availability']}")
    for line in payload["python_sdk"]["notes"]:
        lines.append(f"  {line}")

    lines.extend(["", "External project usage:"])
    lines.append(
        "  copy files required: "
        f"{'yes' if payload['external_project_usage']['copy_files_required'] else 'no'}"
    )
    lines.append(f"  preferred interface: {payload['external_project_usage']['preferred_interface']}")

    lines.extend(["", "Required commands:"])
    for command in payload["required_commands"]:
        lines.append(f"  {command}")

    lines.extend(["", "Verification commands:"])
    for command in payload["verification_commands"]:
        lines.append(f"  {command}")
    return "\n".join(lines)


def render_codex_integration_powershell(payload: dict[str, Any]) -> str:
    """Render a PowerShell-oriented export snippet."""

    skill_targets = ",\n".join(f'  "{target}"' for target in payload["skill"]["targets"])
    plugin_manifest_json = json.dumps(payload["plugin_manifest_inline"], indent=2, ensure_ascii=False)
    mcp_config_json = json.dumps(payload["mcp_config_inline"], indent=2, ensure_ascii=False)
    plugin_manifest_path = payload["plugin_manifest"] or payload["suggested_destinations"]["plugin_manifest"]
    mcp_config_path = payload["mcp_config"] or payload["suggested_destinations"]["mcp_config"]
    return "\n".join(
        [
            "# Agent Reach integration export for Codex on Windows",
            f'$executionContext = "{payload["execution_context"]}"',
            f'$pluginManifestPath = "{plugin_manifest_path}"',
            f'$mcpConfigPath = "{mcp_config_path}"',
            f'$skillSource = "{payload["skill"]["source"]}"',
            "$skillTargets = @(",
            skill_targets,
            ")",
            "",
            "# Write these inline payloads if the file paths above do not exist yet.",
            "$pluginManifestJson = @'",
            plugin_manifest_json,
            "'@",
            "",
            "$mcpConfigJson = @'",
            mcp_config_json,
            "'@",
            "",
            "# Verification commands",
            "agent-reach channels --json",
            "agent-reach doctor --json",
            "agent-reach doctor --json --probe",
            'agent-reach collect --channel github --operation read --input "openai/openai-python" --json',
        ]
    )
