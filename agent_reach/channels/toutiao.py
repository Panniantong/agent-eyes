# -*- coding: utf-8 -*-
"""Toutiao (今日头条) — trending news via free API."""

from .base import Channel


class ToutiaoChannel(Channel):
    name = "toutiao"
    description = "今日头条热点新闻"
    backends = ["Feed API", "Mobile API"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        return "toutiao.com" in urlparse(url).netloc.lower()

    def check(self, config=None):
        import urllib.request
        try:
            req = urllib.request.Request(
                "https://www.toutiao.com/api/pc/feed/?category=news_hot"
                "&utm_source=toutiao&widen=1&max_behot_time=0",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    return "ok", "Feed API 可用，支持热点新闻和分类浏览"
        except Exception:
            pass
        return "warn", "API 暂不可达，可能需要代理"
