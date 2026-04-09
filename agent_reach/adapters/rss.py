# -*- coding: utf-8 -*-
"""RSS collection adapter."""

from __future__ import annotations

import time

import feedparser

from agent_reach.results import CollectionResult, NormalizedItem, build_item, parse_timestamp

from .base import BaseAdapter


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
        items: list[NormalizedItem] = [
            build_item(
                item_id=entry.get("id") or entry.get("link") or entry.get("title") or f"rss-{idx}",
                kind="feed_item",
                title=entry.get("title"),
                url=entry.get("link"),
                text=entry.get("summary") or entry.get("description"),
                author=entry.get("author"),
                published_at=parse_timestamp(
                    entry.get("published_parsed")
                    or entry.get("updated_parsed")
                    or entry.get("published")
                    or entry.get("updated")
                ),
                source=self.channel,
                extras={"feed_title": parsed.feed.get("title")},
            )
            for idx, entry in enumerate(entries)
        ]
        return self.ok_result(
            "read",
            items=items,
            raw=raw,
            meta=self.make_meta(
                value=url,
                limit=limit,
                started_at=started_at,
                feed_title=parsed.feed.get("title"),
            ),
        )
