# -*- coding: utf-8 -*-
"""Helpers for normalized media reference evidence."""

from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import urlparse

_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?P<url>https?://[^)\s]+)\)")
_HTML_IMAGE_RE = re.compile(r"""<img\b[^>]*?\bsrc=["'](?P<url>https?://[^"']+)["']""", re.IGNORECASE)
_IMAGE_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
    ".avif",
)


def _clean_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = unescape(value.strip())
    if not text.startswith(("http://", "https://")):
        return None
    return text


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _text_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_media_reference(
    *,
    type: str,
    url: object,
    relation: str | None = None,
    thumb_url: object = None,
    alt: object = None,
    width: object = None,
    height: object = None,
    duration_seconds: object = None,
    source_field: str | None = None,
    media_type: object = None,
) -> dict[str, Any] | None:
    """Build a normalized linked-media reference."""

    normalized_url = _clean_url(url)
    if not normalized_url:
        return None

    payload: dict[str, Any] = {
        "type": type or "unknown",
        "url": normalized_url,
    }
    relation_text = _text_or_none(relation)
    thumb_text = _clean_url(thumb_url)
    alt_text = _text_or_none(alt)
    source_text = _text_or_none(source_field)
    media_type_text = _text_or_none(media_type)
    width_value = _int_or_none(width)
    height_value = _int_or_none(height)
    duration_value = _int_or_none(duration_seconds)

    if relation_text:
        payload["relation"] = relation_text
    if thumb_text:
        payload["thumb_url"] = thumb_text
    if alt_text:
        payload["alt"] = alt_text
    if width_value is not None:
        payload["width"] = width_value
    if height_value is not None:
        payload["height"] = height_value
    if duration_value is not None:
        payload["duration_seconds"] = duration_value
    if source_text:
        payload["source_field"] = source_text
    if media_type_text:
        payload["media_type"] = media_type_text
    return payload


def dedupe_media_references(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep media references stable and unique while preserving order."""

    seen: set[tuple[object, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for reference in references:
        key = (
            reference.get("type"),
            reference.get("relation"),
            reference.get("url"),
            reference.get("thumb_url"),
            reference.get("source_field"),
            reference.get("media_type"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(reference)
    return deduped


def extract_image_urls(text: str | None) -> list[str]:
    """Extract image URLs from markdown or inline HTML."""

    if not text:
        return []

    urls = [
        match.group("url")
        for match in _MARKDOWN_IMAGE_RE.finditer(text)
    ]
    urls.extend(match.group("url") for match in _HTML_IMAGE_RE.finditer(text))

    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        cleaned = _clean_url(url)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def looks_like_image_url(value: object) -> bool:
    """Best-effort check for common linked image URLs."""

    url = _clean_url(value)
    if not url:
        return False
    path = urlparse(url).path.lower()
    return path.endswith(_IMAGE_EXTENSIONS)
