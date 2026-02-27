# -*- coding: utf-8 -*-
"""Local, non-sensitive telemetry helpers for Agent Reach."""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from agent_reach import __version__
from agent_reach.config import Config


def _parse_bool_env(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return None


def telemetry_enabled(config: Optional[Config] = None) -> bool:
    """Return whether telemetry should be written."""
    env_override = _parse_bool_env(os.environ.get("AGENT_REACH_TELEMETRY"))
    if env_override is not None:
        return env_override

    if config is not None:
        value = config.get("telemetry_enabled")
        if isinstance(value, bool):
            return value

    # Default: on, local file only, no network exfiltration.
    return True


def telemetry_path(config: Optional[Config] = None) -> Path:
    """Get telemetry log path."""
    base_dir = config.config_dir if config is not None else Config.CONFIG_DIR
    return Path(base_dir) / "telemetry.jsonl"


def _base_payload() -> Dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "python": platform.python_version(),
        "os": platform.system(),
    }


def record_cli_event(
    command: str,
    status: str,
    duration_ms: int,
    config: Optional[Config] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Append one local telemetry event (best effort, never raises)."""
    if not telemetry_enabled(config):
        return

    event = _base_payload()
    event.update(
        {
            "event": "cli_command",
            "command": command,
            "status": status,
            "duration_ms": duration_ms,
        }
    )
    if details:
        # Keep details explicit and non-sensitive by design.
        event["details"] = details

    try:
        path = telemetry_path(config)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # Telemetry should never interrupt user workflows.
        return
