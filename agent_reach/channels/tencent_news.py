# -*- coding: utf-8 -*-
"""Tencent News (腾讯新闻) — trending news via free API."""

from .base import Channel


class TencentNewsChannel(Channel):
    name = "tencent_news"
    description = "腾讯新闻热点资讯"
    backends = ["Hot Ranking API", "Article SSR"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        return any(d in host for d in [
            "new.qq.com", "news.qq.com",
            "view.inews.qq.com", "xw.qq.com",
        ])

    def check(self, config=None):
        import urllib.request
        try:
            req = urllib.request.Request(
                "https://i.news.qq.com/gw/event/pc_hot_ranking_list"
                "?ids_hash=&offset=0&page_size=5",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    return "ok", "热榜 API 可用，支持热点排行和文章阅读"
        except Exception:
            pass
        return "warn", "API 暂不可达，可能需要代理"
