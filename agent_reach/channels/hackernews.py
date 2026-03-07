# -*- coding: utf-8 -*-
"""Hacker News — tech community via official Firebase API + Algolia search."""

from .base import Channel


class HackerNewsChannel(Channel):
    name = "hackernews"
    description = "Hacker News 技术社区"
    backends = ["Firebase API", "Algolia Search"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        return "news.ycombinator.com" in host or "hn.algolia.com" in host

    def check(self, config=None):
        import json
        import urllib.request
        try:
            req = urllib.request.Request(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    ids = json.loads(r.read())
                    if ids:
                        return "ok", f"Firebase API 可用，{len(ids)} top stories"
        except Exception:
            pass
        return "warn", "API 暂不可达，可能需要代理"
