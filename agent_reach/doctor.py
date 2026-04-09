# -*- coding: utf-8 -*-
"""Health checks and machine-readable diagnostics for supported channels."""

from __future__ import annotations

from typing import Dict

from agent_reach.channels import get_all_channels
from agent_reach.config import Config
from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp


def check_all(config: Config, probe: bool = False) -> Dict[str, dict]:
    """Collect health information from every registered channel."""

    results: Dict[str, dict] = {}
    for channel in get_all_channels():
        try:
            if probe and channel.supports_probe:
                status, message = channel.probe(config)
            else:
                status, message = channel.check(config)
        except Exception as exc:
            status, message = "error", f"Health check crashed: {exc}"

        contract = (
            channel.to_contract()
            if hasattr(channel, "to_contract")
            else {
                "name": channel.name,
                "description": getattr(channel, "description", channel.name),
                "tier": getattr(channel, "tier", 0),
                "backends": list(getattr(channel, "backends", [])),
                "auth_kind": getattr(channel, "auth_kind", "none"),
                "entrypoint_kind": getattr(channel, "entrypoint_kind", "cli"),
                "operations": list(getattr(channel, "operations", [])),
                "required_commands": list(getattr(channel, "required_commands", [])),
                "host_patterns": list(getattr(channel, "host_patterns", [])),
                "example_invocations": list(getattr(channel, "example_invocations", [])),
                "supports_probe": bool(getattr(channel, "supports_probe", False)),
                "install_hints": list(getattr(channel, "install_hints", [])),
            }
        )

        results[channel.name] = {
            **contract,
            "status": status,
            "message": message,
        }
    return results


def summarize_results(results: Dict[str, dict]) -> dict:
    """Build a stable summary block for machine-readable output."""

    values = list(results.values())
    core = [item for item in values if item["tier"] == 0]
    optional = [item for item in values if item["tier"] != 0]
    return {
        "total": len(values),
        "ready": sum(1 for item in values if item["status"] == "ok"),
        "warnings": sum(1 for item in values if item["status"] == "warn"),
        "off": sum(1 for item in values if item["status"] == "off"),
        "errors": sum(1 for item in values if item["status"] == "error"),
        "not_ready": [item["name"] for item in values if item["status"] != "ok"],
        "core": {
            "total": len(core),
            "ready": sum(1 for item in core if item["status"] == "ok"),
        },
        "optional": {
            "total": len(optional),
            "ready": sum(1 for item in optional if item["status"] == "ok"),
        },
    }


def doctor_exit_code(results: Dict[str, dict]) -> int:
    """Return the standardized exit code for doctor results."""

    core = [item for item in results.values() if item["tier"] == 0]
    if any(item["status"] in {"off", "error"} for item in core):
        return 2
    if any(item["status"] != "ok" for item in results.values()):
        return 1
    return 0


def make_doctor_payload(results: Dict[str, dict], probe: bool = False) -> dict:
    """Build a machine-readable doctor payload."""

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "probe": probe,
        "summary": summarize_results(results),
        "channels": list(results.values()),
    }


def format_report(results: Dict[str, dict], probe: bool = False) -> str:
    """Render a compact terminal-friendly health report."""

    try:
        from rich.markup import escape
    except ImportError:

        def escape(value: str) -> str:
            return value

    def render_line(result: dict) -> str:
        status = result["status"]
        label_name = result.get("description") or result.get("name", "unknown")
        label = f"[bold]{escape(label_name)}[/bold]: {escape(result['message'])}"
        if status == "ok":
            return f"  [green][OK][/green] {label}"
        if status == "warn":
            return f"  [yellow][WARN][/yellow] {label}"
        if status == "off":
            return f"  [red][OFF][/red] {label}"
        return f"  [red][ERR][/red] {label}"

    summary = summarize_results(results)
    lines = [
        "[bold cyan]Agent Reach Health[/bold cyan]",
        "[cyan]========================================[/cyan]",
    ]
    if probe:
        lines.append("[cyan]Mode: lightweight live probes enabled[/cyan]")
    lines.extend(["", "[bold]Core channels[/bold]"])

    core = [result for result in results.values() if result["tier"] == 0]
    optional = [result for result in results.values() if result["tier"] != 0]
    for result in core:
        lines.append(render_line(result))

    if optional:
        lines.extend(["", "[bold]Optional channels[/bold]"])
        for result in optional:
            lines.append(render_line(result))

    lines.extend(["", f"Summary: [bold]{summary['ready']}/{summary['total']}[/bold] channels ready"])
    if summary["not_ready"]:
        labels = [
            item.get("description") or item.get("name", "unknown")
            for item in results.values()
            if item["status"] != "ok"
        ]
        lines.append(f"Not ready: {', '.join(labels)}")

    return "\n".join(lines)
