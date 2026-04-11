# -*- coding: utf-8 -*-
"""RSS collection adapter."""

from __future__ import annotations

import time

import feedparser

from agent_reach.media_references import build_media_reference, dedupe_media_references
from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    build_pagination_meta,
    parse_timestamp,
)
from agent_reach.source_hints import rss_source_hints

from .base import BaseAdapter


def _entry_media_references(entry: dict) -> list[dict]:
    references = []
    for media in entry.get("media_thumbnail") or []:
        if not isinstance(media, dict):
            continue
        reference = build_media_reference(
            type="image",
            url=media.get("url"),
            relation="thumbnail",
            width=media.get("width"),
            height=media.get("height"),
            source_field="media_thumbnail[]",
        )
        if reference is not None:
            references.append(reference)
    for media in entry.get("media_content") or []:
        if not isinstance(media, dict):
            continue
        medium = str(media.get("medium") or media.get("type") or "")
        reference = build_media_reference(
            type="image" if "image" in medium else "unknown",
            media_type=medium or None,
            url=media.get("url"),
            relation="media_content",
            width=media.get("width"),
            height=media.get("height"),
            source_field="media_content[]",
        )
        if reference is not None:
            references.append(reference)
    for link in entry.get("links") or []:
        if not isinstance(link, dict):
            continue
        if str(link.get("rel") or "").lower() not in {"enclosure", "thumbnail"}:
            continue
        media_type = str(link.get("type") or "")
        reference = build_media_reference(
            type="image" if media_type.startswith("image/") else "unknown",
            media_type=media_type or None,
            url=link.get("href"),
            relation=str(link.get("rel") or "enclosure"),
            source_field="links[]",
        )
        if reference is not None:
            references.append(reference)
    return dedupe_media_references(references)


class RSSAdapter(BaseAdapter):
    """Read RSS and Atom feeds through feedparser."""

    channel = "rss"
    operations = ("read",)

    def read(self, url: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:
            return self.error_result(
                "read",
                code="parse_failed",
                message=f"RSS read failed: {exc}",
                meta=self.make_meta(value=url, limit=limit, started_at=started_at),
            )

        entries = [dict(entry) for entry in parsed.entries[:limit]]
        raw = {
            "feed": dict(parsed.feed),
            "entries": entries,
            "bozo": bool(getattr(parsed, "bozo", False)),
            "status": getattr(parsed, "status", None),
        }
        items: list[NormalizedItem] = []
        for idx, entry in enumerate(entries):
            published_at = parse_timestamp(
                entry.get("published_parsed")
                or entry.get("updated_parsed")
                or entry.get("published")
                or entry.get("updated")
            )
            items.append(
                build_item(
                    item_id=entry.get("id")
                    or entry.get("link")
                    or entry.get("title")
                    or f"rss-{idx}",
                    kind="feed_item",
                    title=entry.get("title"),
                    url=entry.get("link"),
                    text=entry.get("summary") or entry.get("description"),
                    author=entry.get("author"),
                    published_at=published_at,
                    source=self.channel,
                    extras={
                        "feed_title": parsed.feed.get("title"),
                        "media_references": _entry_media_references(entry),
                        "source_hints": rss_source_hints(published_at),
                    },
                )
            )
        return self.ok_result(
            "read",
            items=items,
            raw=raw,
            meta=self.make_meta(
                value=url,
                limit=limit,
                started_at=started_at,
                feed_title=parsed.feed.get("title"),
                **build_pagination_meta(
                    limit=limit,
                    page_size=len(getattr(parsed, "entries", [])),
                    pages_fetched=1,
                    has_more=len(getattr(parsed, "entries", [])) > len(entries),
                    total_available=len(getattr(parsed, "entries", [])),
                ),
            ),
        )
