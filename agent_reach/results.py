# -*- coding: utf-8 -*-
"""Shared result schema helpers for external collection APIs."""

from __future__ import annotations

from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from time import struct_time
from typing import Any, TypedDict

from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp


class NormalizedItem(TypedDict):
    """A normalized content item that can be consumed by external projects."""

    id: str
    kind: str
    title: str | None
    url: str | None
    text: str | None
    author: str | None
    published_at: str | None
    source: str
    extras: dict[str, Any]


class CollectionError(TypedDict):
    """A stable external-facing error shape."""

    code: str
    message: str
    details: dict[str, Any]


class CollectionResult(TypedDict):
    """A stable external-facing collection result."""

    ok: bool
    channel: str
    operation: str
    items: list[NormalizedItem]
    raw: Any
    meta: dict[str, Any]
    error: CollectionError | None


def build_item(
    *,
    item_id: str,
    kind: str,
    title: str | None,
    url: str | None,
    text: str | None,
    author: str | None,
    published_at: str | None,
    source: str,
    extras: dict[str, Any] | None = None,
) -> NormalizedItem:
    """Build a normalized item."""

    return {
        "id": item_id,
        "kind": kind,
        "title": title,
        "url": url,
        "text": text,
        "author": author,
        "published_at": published_at,
        "source": source,
        "extras": extras or {},
    }


def build_result(
    *,
    ok: bool,
    channel: str,
    operation: str,
    items: list[NormalizedItem] | None = None,
    raw: Any = None,
    meta: dict[str, Any] | None = None,
    error: CollectionError | None = None,
) -> CollectionResult:
    """Build a collection result envelope."""

    payload_meta = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        **(meta or {}),
    }
    payload_meta.setdefault("count", len(items or []))
    return {
        "ok": ok,
        "channel": channel,
        "operation": operation,
        "items": items or [],
        "raw": raw,
        "meta": payload_meta,
        "error": error,
    }


def build_error(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> CollectionError:
    """Build a stable collection error."""

    return {
        "code": code,
        "message": message,
        "details": details or {},
    }


def parse_timestamp(value: Any) -> str | None:
    """Best-effort conversion of common timestamp shapes into ISO-8601."""

    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, struct_time):
        return datetime(*value[:6], tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            try:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            except ValueError:
                pass
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        except ValueError:
            pass
        if len(text) == 8 and text.isdigit():
            try:
                parsed = datetime.strptime(text, "%Y%m%d").replace(tzinfo=timezone.utc)
                return parsed.isoformat().replace("+00:00", "Z")
            except ValueError:
                pass
        try:
            parsed = parsedate_to_datetime(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        except (TypeError, ValueError):
            return text
    return str(value)


def derive_title_from_text(text: str | None, fallback: str | None = None, max_length: int = 80) -> str | None:
    """Return a compact title derived from text when a native title is unavailable."""

    if text:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if first_line:
            return first_line[:max_length]
    return fallback
