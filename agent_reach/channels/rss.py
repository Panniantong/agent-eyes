# -*- coding: utf-8 -*-
"""RSS — check if feedparser is available."""

import importlib.util

from .base import Channel


class RSSChannel(Channel):
    name = "rss"
    description = "RSS/Atom 订阅源"
    backends = ["feedparser"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        return any(x in url.lower() for x in ["/feed", "/rss", ".xml", "atom"])

    def check(self, config=None):
        if importlib.util.find_spec("feedparser") is not None:
            return "ok", "可读取 RSS/Atom 源"
        return "off", "feedparser 未安装。安装：pip install feedparser"
