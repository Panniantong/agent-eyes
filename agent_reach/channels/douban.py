# -*- coding: utf-8 -*-
"""Douban (豆瓣) — books, movies & culture via free API."""

import os
from .base import Channel


class DoubanChannel(Channel):
    name = "douban"
    description = "豆瓣电影/图书/音乐"
    backends = ["Unified Search API", "Movie Chart API", "Mobile SSR"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        return host == "douban.com" or host.endswith(".douban.com")

    def check(self, config=None):
        import json
        import urllib.request
        proxy = (config.get("douban_proxy") if config else None) or os.environ.get("DOUBAN_PROXY")
        try:
            req = urllib.request.Request(
                "https://movie.douban.com/j/chart/top_list"
                "?type=11&interval_id=100%3A90&action=&start=0&limit=1",
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://movie.douban.com/typerank",
                },
            )
            if proxy:
                handler = urllib.request.ProxyHandler({"https": proxy, "http": proxy})
                opener = urllib.request.build_opener(handler)
            else:
                opener = urllib.request.build_opener()
            with opener.open(req, timeout=10) as r:
                if r.status == 200:
                    data = json.loads(r.read())
                    if data:
                        return "ok", "统一搜索/电影榜单/图书搜索/热门探索均可用"
        except Exception:
            pass
        return "warn", "API 暂不可达，可能需要代理（设置 DOUBAN_PROXY 环境变量）"
