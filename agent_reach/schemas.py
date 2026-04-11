# -*- coding: utf-8 -*-
"""Shared schema helpers for machine-readable Agent Reach output."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib.resources import files

SCHEMA_VERSION = "2026-04-10"


def utc_timestamp() -> str:
    """Return an RFC3339 UTC timestamp for JSON payloads."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collection_result_schema() -> dict:
    """Return the packaged JSON Schema for CollectionResult envelopes."""

    text = files("agent_reach.schema_files").joinpath("collection_result.schema.json").read_text(encoding="utf-8")
    return json.loads(text)
