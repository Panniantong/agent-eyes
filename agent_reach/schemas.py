# -*- coding: utf-8 -*-
"""Shared schema helpers for machine-readable Agent Reach output."""

from __future__ import annotations

from datetime import datetime, timezone

SCHEMA_VERSION = "2026-04-10"


def utc_timestamp() -> str:
    """Return an RFC3339 UTC timestamp for JSON payloads."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
