# -*- coding: utf-8 -*-
"""RSS feeds — via feedparser (free, pip dependency).

Backend: feedparser (https://github.com/kurtmckee/feedparser)
Swap to: any RSS parser
"""

import feedparser
from urllib.parse import urlparse
from .base import Channel, ReadResult


class RSSChannel(Channel):
    name = "rss"
    description = "RSS/Atom 订阅源"
    backends = ["feedparser"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        lower = url.lower()
        domain = urlparse(url).netloc.lower()
        return (lower.endswith(".xml") or "/rss" in lower or "/feed" in lower
                or "/atom" in lower or "rss" in domain)

    async def read(self, url: str, config=None) -> ReadResult:
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            raise ValueError(f"Failed to parse RSS feed: {url}")

        if not feed.entries:
            raise ValueError(f"No entries in RSS feed: {url}")

        # Return latest entry
        entry = feed.entries[0]
        content = entry.get("summary", "") or entry.get("description", "")

        # If multiple entries, summarize all
        if len(feed.entries) > 1:
            lines = [f"# {feed.feed.get('title', 'RSS Feed')}\n"]
            for i, e in enumerate(feed.entries[:20], 1):
                title = e.get("title", "Untitled")
                link = e.get("link", "")
                summary = e.get("summary", "")[:200]
                lines.append(f"## {i}. {title}")
                lines.append(f"🔗 {link}")
                if summary:
                    lines.append(summary)
                lines.append("")
            content = "\n".join(lines)

        return ReadResult(
            title=feed.feed.get("title", entry.get("title", url)),
            content=content,
            url=url,
            platform="rss",
        )
