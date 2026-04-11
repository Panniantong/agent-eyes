# -*- coding: utf-8 -*-
"""RSS channel checks."""

from __future__ import annotations

from .base import Channel


class RSSChannel(Channel):
    name = "rss"
    description = "RSS and Atom feeds"
    backends = ["feedparser"]
    auth_kind = "none"
    entrypoint_kind = "python"
    operations = ["read"]
    operation_inputs = {"read": "url"}
    host_patterns = ["*feed*", "*.xml", "*atom*"]
    example_invocations = [
        'agent-reach collect --channel rss --operation read --input "https://hnrss.org/frontpage" --limit 10 --json',
    ]
    supports_probe = True
    install_hints = [
        "feedparser is installed as part of the Python package dependencies.",
    ]

    def can_handle(self, url: str) -> bool:
        lowered = url.lower()
        return any(marker in lowered for marker in ["/feed", "/rss", ".xml", "atom"])

    def check(self, config=None):
        try:
            import feedparser  # noqa: F401
        except ImportError:
            return "off", "feedparser is missing. Install it with pip install feedparser"
        return "ok", "Ready to parse RSS and Atom feeds"

    def probe(self, config=None):
        try:
            import feedparser
        except ImportError:
            return "off", "feedparser is missing. Install it with pip install feedparser"

        try:
            parsed = feedparser.parse("https://hnrss.org/frontpage")
        except Exception as exc:
            return "warn", f"RSS probe failed: {exc}"

        title = getattr(parsed, "feed", {}).get("title", "")
        if title and getattr(parsed, "entries", []):
            return "ok", f"Live RSS probe succeeded: {title}"
        return "warn", "RSS probe returned no feed entries"
