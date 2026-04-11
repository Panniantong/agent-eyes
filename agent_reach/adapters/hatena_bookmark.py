# -*- coding: utf-8 -*-
"""Hatena Bookmark collection adapter."""

from __future__ import annotations

import time
import warnings
from datetime import datetime, timezone
from urllib.parse import urlparse

from agent_reach.media_references import build_media_reference, dedupe_media_references
from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    parse_timestamp,
)

from .base import BaseAdapter

_UA = "agent-reach/1.4.0 (+https://github.com/iwachacha/Agent-Reach)"
_ENTRY_API = "https://b.hatena.ne.jp/entry/json/"
_COUNT_API = "https://bookmark.hatenaapis.com/count/entry"


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


def _normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def _parse_hatena_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y/%m/%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return parse_timestamp(value)
    return parsed.isoformat().replace("+00:00", "Z")


def _fallback_title(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url


class HatenaBookmarkAdapter(BaseAdapter):
    """Read Hatena Bookmark entry metadata for a target URL."""

    channel = "hatena_bookmark"
    operations = ("read",)

    def read(self, url: str, limit: int | None = 5) -> CollectionResult:
        started_at = time.perf_counter()
        normalized = _normalize_url(url)
        requests = _import_requests()
        item_limit = max(limit or 1, 1)
        try:
            response = requests.get(
                _ENTRY_API,
                params={"url": normalized},
                headers={"User-Agent": _UA, "Accept": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return self.error_result(
                "read",
                code="http_error",
                message=f"Hatena Bookmark read failed: {exc}",
                meta=self.make_meta(value=normalized, limit=limit, started_at=started_at),
            )

        try:
            raw = response.json()
        except ValueError:
            return self.error_result(
                "read",
                code="invalid_response",
                message="Hatena Bookmark returned a non-JSON payload",
                raw=response.text,
                meta=self.make_meta(value=normalized, limit=limit, started_at=started_at),
            )

        if raw is None:
            count = self._bookmark_count(normalized)
            item = build_item(
                item_id=normalized,
                kind="page_reaction",
                title=_fallback_title(normalized),
                url=normalized,
                text=f"Hatena Bookmark count: {count}",
                author=None,
                published_at=None,
                source=self.channel,
                extras={
                    "bookmark_count": count,
                    "entry_url": None,
                    "related_count": 0,
                },
            )
            return self.ok_result(
                "read",
                items=[item],
                raw={"entry": None, "count": count},
                meta=self.make_meta(value=normalized, limit=limit, started_at=started_at),
            )

        bookmarks = raw.get("bookmarks") or []
        related = raw.get("related") or []
        latest_bookmark = bookmarks[0] if bookmarks else {}
        comment_count = sum(1 for bookmark in bookmarks if (bookmark.get("comment") or "").strip())

        items: list[NormalizedItem] = [
            build_item(
                item_id=str(raw.get("eid") or normalized),
                kind="page_reaction",
                title=raw.get("title") or _fallback_title(normalized),
                url=raw.get("url") or normalized,
                text=f"Hatena Bookmark count: {raw.get('count', 0)}",
                author=None,
                published_at=_parse_hatena_timestamp(latest_bookmark.get("timestamp")),
                source=self.channel,
                extras={
                    "entry_url": raw.get("entry_url"),
                    "bookmark_count": raw.get("count"),
                    "comment_count": comment_count,
                    "screenshot": raw.get("screenshot"),
                    "media_references": dedupe_media_references(
                        [
                            reference
                            for reference in [
                                build_media_reference(
                                    type="image",
                                    url=raw.get("screenshot"),
                                    relation="screenshot",
                                    source_field="screenshot",
                                )
                            ]
                            if reference is not None
                        ]
                    ),
                },
            )
        ]

        related_slots = max(item_limit - 1, 0)
        for idx, entry in enumerate(related[:related_slots]):
            items.append(
                build_item(
                    item_id=str(entry.get("eid") or f"related-{idx}"),
                    kind="related_page",
                    title=entry.get("title"),
                    url=entry.get("url") or entry.get("entry_url"),
                    text=f"Hatena Bookmark count: {entry.get('count', 0)}",
                    author=None,
                    published_at=None,
                    source=self.channel,
                    extras={
                        "entry_url": entry.get("entry_url"),
                        "bookmark_count": entry.get("count"),
                    },
                )
            )

        return self.ok_result(
            "read",
            items=items,
            raw=raw,
            meta=self.make_meta(
                value=normalized,
                limit=limit,
                started_at=started_at,
                related_included=len(items) - 1,
                total_related=len(related),
            ),
        )

    def _bookmark_count(self, url: str) -> int:
        requests = _import_requests()
        try:
            response = requests.get(
                _COUNT_API,
                params={"url": url},
                headers={"User-Agent": _UA, "Accept": "text/plain"},
                timeout=30,
            )
            response.raise_for_status()
            return int((response.text or "0").strip() or "0")
        except Exception:
            return 0
