# -*- coding: utf-8 -*-
"""V2EX — check if the public API is reachable (no auth required)."""

from .base import Channel


class V2EXChannel(Channel):
    name = "v2ex"
    description = "V2EX 节点、主题与回复"
    backends = ["V2EX API (public)"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "v2ex.com" in d

    def check(self, config=None):
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1",
                headers={"User-Agent": "agent-reach/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    return "ok", "公开 API 可用（热门主题、节点浏览、主题详情、用户信息）"
        except Exception as e:
            return "warn", f"V2EX API 连接失败（可能需要代理）：{e}"
        return "warn", "V2EX API 响应异常，检查网络或代理配置"
