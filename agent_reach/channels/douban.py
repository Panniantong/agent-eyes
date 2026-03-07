# -*- coding: utf-8 -*-
"""Douban (豆瓣) — books, movies & culture via free API."""

from .base import Channel


class DoubanChannel(Channel):
    name = "douban"
    description = "豆瓣电影/图书/小组"
    backends = ["Book Suggest API", "Movie Chart API", "Mobile SSR"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        return host.endswith("douban.com")

    def check(self, config=None):
        import json
        import urllib.request
        try:
            req = urllib.request.Request(
                "https://movie.douban.com/j/chart/top_list"
                "?type=11&interval_id=100%3A90&action=&start=0&limit=1",
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://movie.douban.com/typerank",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    data = json.loads(r.read())
                    if data:
                        return "ok", "Movie Chart API 可用，支持图书搜索和电影榜单"
        except Exception:
            pass
        return "warn", "API 暂不可达，可能需要代理"
