# -*- coding: utf-8 -*-
"""Facebook — check connectivity and configuration."""

import os
import urllib.request
from .base import Channel

_TIMEOUT = 10


def _facebook_reachable() -> bool:
    """Return True if Facebook is reachable."""
    url = "https://www.facebook.com/"
    req = urllib.request.Request(url, headers={"User-Agent": "agent-reach/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False


class FacebookChannel(Channel):
    name = "facebook"
    description = "Facebook 帖子和评论"
    backends = ["Facebook Graph API"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "facebook.com" in d or "fb.com" in d or "fb.watch" in d

    def check(self, config=None):
        token = (config.get("facebook_token") if config else None) or os.environ.get("FACEBOOK_TOKEN")
        if not token:
            return "warn", (
                "未配置 Facebook Token。请设置环境变量：\n"
                "  export FACEBOOK_TOKEN=your_access_token"
            )
        if _facebook_reachable():
            return "ok", "Facebook 可达，Token 已配置"
        return "warn", "Facebook 无法连接，请检查网络或代理配置"
