# -*- coding: utf-8 -*-
"""Health checks and machine-readable diagnostics for supported channels."""

from __future__ import annotations

from typing import Any, Callable, Dict, Sequence

from agent_reach.channels import get_all_channels
from agent_reach.config import Config
from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp


def _normalize_health_result(result: object) -> tuple[str, str, dict[str, Any]]:
    """Accept legacy 2-tuples and newer 3-tuples with extra machine-readable data."""

    if not isinstance(result, tuple):
        raise TypeError("health checks must return a tuple")
    if len(result) == 2:
        status, message = result
        return status, message, {}
    if len(result) == 3:
        status, message, extra = result
        return status, message, extra if isinstance(extra, dict) else {}
    raise ValueError("health checks must return a 2-tuple or 3-tuple")


def _default_operation_statuses(contract: dict, status: str, message: str) -> dict[str, dict[str, str]]:
    """Provide operation-level health when a channel has no richer diagnostic data."""

    return {
        operation: {
            "status": status,
            "message": message,
            "diagnostic_basis": "channel_health",
        }
        for operation in contract.get("operations", [])
    }


def _default_probe_state(contract: dict, *, probe: bool) -> dict[str, object]:
    """Provide probe-run diagnostics even when a channel returns only a basic health tuple."""

    supports_probe = bool(contract.get("supports_probe"))
    operations = list(contract.get("operations", []))
    probe_operations = list(contract.get("probe_operations") or (operations if supports_probe else []))
    if not supports_probe:
        return {
            "probed_operations": [],
            "unprobed_operations": [],
            "probe_run_coverage": "unsupported",
        }
    if not probe:
        return {
            "probed_operations": [],
            "unprobed_operations": operations,
            "probe_run_coverage": "not_run",
        }
    return {
        "probed_operations": probe_operations,
        "unprobed_operations": [operation for operation in operations if operation not in probe_operations],
        "probe_run_coverage": "full" if set(probe_operations) == set(operations) else "partial",
    }


def check_all(config: Config, probe: bool = False) -> Dict[str, dict]:
    """Collect health information from every registered channel."""

    results: Dict[str, dict] = {}
    for channel in get_all_channels():
        extra: dict[str, Any] = {}
        try:
            if probe and channel.supports_probe:
                method = getattr(channel, "probe_detailed", channel.probe)
                status, message, extra = _normalize_health_result(method(config))
            else:
                method = getattr(channel, "check_detailed", channel.check)
                status, message, extra = _normalize_health_result(method(config))
        except Exception as exc:
            status, message = "error", f"Health check crashed: {exc}"

        contract = (
            channel.to_contract()
            if hasattr(channel, "to_contract")
            else {
                "name": channel.name,
                "description": getattr(channel, "description", channel.name),
                "backends": list(getattr(channel, "backends", [])),
                "auth_kind": getattr(channel, "auth_kind", "none"),
                "entrypoint_kind": getattr(channel, "entrypoint_kind", "cli"),
                "operations": list(getattr(channel, "operations", [])),
                "required_commands": list(getattr(channel, "required_commands", [])),
                "host_patterns": list(getattr(channel, "host_patterns", [])),
                "example_invocations": list(getattr(channel, "example_invocations", [])),
                "supports_probe": bool(getattr(channel, "supports_probe", False)),
                "install_hints": list(getattr(channel, "install_hints", [])),
                "operation_contracts": getattr(channel, "get_operation_contracts", lambda: {})(),
            }
        )

        payload = {
            **contract,
            "status": status,
            "message": message,
        }
        if contract.get("operations") and "operation_statuses" not in extra:
            payload["operation_statuses"] = _default_operation_statuses(contract, status, message)
        probe_state = _default_probe_state(contract, probe=probe)
        for key, value in probe_state.items():
            if key not in extra:
                payload[key] = value
        reserved = set(payload)
        payload.update({key: value for key, value in extra.items() if key not in reserved})
        results[channel.name] = payload
    return results


def _not_ready_names(items: list[dict]) -> list[str]:
    return [item["name"] for item in items if item["status"] != "ok"]


def _normalize_required_channels(
    results: Dict[str, dict],
    *,
    required_channels: Sequence[str] | None = None,
    require_all: bool = False,
) -> list[str]:
    available = list(results)
    available_set = set(available)
    if require_all:
        return available

    normalized: list[str] = []
    for name in required_channels or ():
        if name not in available_set:
            raise ValueError(f"Unknown required channel: {name}")
        if name not in normalized:
            normalized.append(name)
    return normalized


def _required_and_informational_items(
    results: Dict[str, dict],
    *,
    required_channels: Sequence[str] | None = None,
    require_all: bool = False,
) -> tuple[list[dict], list[dict], list[str]]:
    normalized_required = _normalize_required_channels(
        results,
        required_channels=required_channels,
        require_all=require_all,
    )
    required_set = set(normalized_required)
    required_items = [results[name] for name in normalized_required]
    informational_items = [
        item
        for name, item in results.items()
        if name not in required_set
    ]
    return required_items, informational_items, normalized_required


def _probe_attention(results: Dict[str, dict], *, probe: bool = False) -> list[dict[str, Any]]:
    attention: list[dict[str, Any]] = []
    for item in results.values():
        if not item.get("supports_probe"):
            continue
        probe_coverage = str(item.get("probe_coverage") or "none")
        probe_run_coverage = str(item.get("probe_run_coverage") or "not_run")
        include = probe_coverage != "full" or (probe and probe_run_coverage != "full")
        if not include:
            continue
        attention.append(
            {
                "name": item.get("name"),
                "probe_coverage": probe_coverage,
                "probe_run_coverage": probe_run_coverage,
                "unprobed_operations": [str(op) for op in item.get("unprobed_operations") or []],
            }
        )
    return attention


def summarize_results(
    results: Dict[str, dict],
    *,
    probe: bool = False,
    required_channels: Sequence[str] | None = None,
    require_all: bool = False,
) -> dict:
    """Build a stable summary block for machine-readable output."""

    values = list(results.values())
    required_items, informational_items, normalized_required = _required_and_informational_items(
        results,
        required_channels=required_channels,
        require_all=require_all,
    )
    exit_code = doctor_exit_code(
        results,
        required_channels=required_channels,
        require_all=require_all,
    )
    probe_attention = _probe_attention(results, probe=probe)
    readiness_mode = "all" if require_all else ("selected" if normalized_required else "none")
    return {
        "total": len(values),
        "ready": sum(1 for item in values if item["status"] == "ok"),
        "warnings": sum(1 for item in values if item["status"] == "warn"),
        "off": sum(1 for item in values if item["status"] == "off"),
        "errors": sum(1 for item in values if item["status"] == "error"),
        "not_ready": [item["name"] for item in values if item["status"] != "ok"],
        "readiness_mode": readiness_mode,
        "required_channels": normalized_required,
        "exit_code": exit_code,
        "required_not_ready": _not_ready_names(required_items),
        "informational_not_ready": _not_ready_names(informational_items),
        "required": {
            "total": len(required_items),
            "ready": sum(1 for item in required_items if item["status"] == "ok"),
        },
        "informational": {
            "total": len(informational_items),
            "ready": sum(1 for item in informational_items if item["status"] == "ok"),
        },
        "probe_attention": probe_attention,
    }


def doctor_exit_code(
    results: Dict[str, dict],
    *,
    required_channels: Sequence[str] | None = None,
    require_all: bool = False,
) -> int:
    """Return the standardized exit code for doctor results."""

    required_items, informational_items, _normalized_required = _required_and_informational_items(
        results,
        required_channels=required_channels,
        require_all=require_all,
    )
    if any(item["status"] in {"off", "error"} for item in required_items):
        return 2
    if any(item["status"] == "warn" for item in required_items):
        return 1
    if any(item["status"] == "error" for item in informational_items):
        return 1
    return 0


def make_doctor_payload(
    results: Dict[str, dict],
    probe: bool = False,
    *,
    required_channels: Sequence[str] | None = None,
    require_all: bool = False,
) -> dict:
    """Build a machine-readable doctor payload."""

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "probe": probe,
        "summary": summarize_results(
            results,
            probe=probe,
            required_channels=required_channels,
            require_all=require_all,
        ),
        "channels": list(results.values()),
    }


def format_report(
    results: Dict[str, dict],
    probe: bool = False,
    *,
    required_channels: Sequence[str] | None = None,
    require_all: bool = False,
) -> str:
    """Render a compact terminal-friendly health report."""

    escape_markup: Callable[[str], str]
    try:
        from rich.markup import escape as rich_escape

        escape_markup = rich_escape
    except ImportError:

        def escape_markup(value: str) -> str:
            return value

    normalized_required = _normalize_required_channels(
        results,
        required_channels=required_channels,
        require_all=require_all,
    )
    required_set = set(normalized_required)

    def render_line(result: dict) -> str:
        status = result["status"]
        label_name = result.get("description") or result.get("name", "unknown")
        channel_name = result.get("name", "")
        required_suffix = " (required)" if channel_name in required_set else ""
        label = f"[bold]{escape_markup(label_name)}[/bold]: {escape_markup(result['message'])}"
        if status == "ok":
            return f"  [green][OK][/green] {label}{required_suffix}"
        if status == "warn":
            return f"  [yellow][WARN][/yellow] {label}{required_suffix}"
        if status == "off":
            return f"  [red][OFF][/red] {label}{required_suffix}"
        return f"  [red][ERR][/red] {label}{required_suffix}"

    summary = summarize_results(
        results,
        probe=probe,
        required_channels=required_channels,
        require_all=require_all,
    )
    lines = [
        "[bold cyan]Agent Reach Health[/bold cyan]",
        "[cyan]========================================[/cyan]",
    ]
    if probe:
        lines.append("[cyan]Mode: lightweight live probes enabled[/cyan]")
    if summary["readiness_mode"] == "all":
        lines.append("[cyan]Readiness policy: all channels required[/cyan]")
    elif summary["required_channels"]:
        lines.append(
            "[cyan]Readiness policy: required channels = "
            f"{escape_markup(', '.join(summary['required_channels']))}[/cyan]"
        )
    else:
        lines.append("[cyan]Readiness policy: diagnostic only (no required channels)[/cyan]")
    lines.extend(["", "[bold]Channels[/bold]"])

    for result in results.values():
        lines.append(render_line(result))

    lines.extend(["", f"Summary: [bold]{summary['ready']}/{summary['total']}[/bold] channels ready"])
    if summary["required_not_ready"]:
        labels = [
            item.get("description") or item.get("name", "unknown")
            for item in results.values()
            if item["name"] in summary["required_not_ready"]
        ]
        lines.append(f"Required not ready: {', '.join(labels)}")
    if summary["informational_not_ready"]:
        labels = [
            item.get("description") or item.get("name", "unknown")
            for item in results.values()
            if item["name"] in summary["informational_not_ready"]
        ]
        lines.append(f"Informational only: {', '.join(labels)}")
    if summary["probe_attention"]:
        lines.append("Probe attention:")
        for item in summary["probe_attention"]:
            label = next(
                (
                    result.get("description") or result.get("name", "unknown")
                    for result in results.values()
                    if result.get("name") == item["name"]
                ),
                item["name"] or "unknown",
            )
            unprobed = ", ".join(item["unprobed_operations"]) if item["unprobed_operations"] else "none"
            lines.append(
                "  "
                f"{label} (coverage: {item['probe_coverage']}; "
                f"run: {item['probe_run_coverage']}; "
                f"unprobed: {unprobed})"
            )

    return "\n".join(lines)
