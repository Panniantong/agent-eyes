# -*- coding: utf-8 -*-
"""Discord — check connectivity and configuration."""

import os
import urllib.request
from .base import Channel

_TIMEOUT = 10


def _discord_reachable() -> bool:
    """Return True if Discord API is reachable."""
    url = "https://discord.com/api/v10/gateway"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False


class DiscordChannel(Channel):
    name = "discord"
    description = "Discord 服务器消息和频道"
    backends = ["Discord API"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "discord.com" in d or "discord.gg" in d

    def check(self, config=None):
        token = (config.get("discord_token") if config else None) or os.environ.get("DISCORD_TOKEN")
        if not token:
            return "warn", (
                "未配置 Discord Bot Token。请设置环境变量：\n"
                "  export DISCORD_TOKEN=your_bot_token"
            )
        if _discord_reachable():
            return "ok", "Discord API 可达，Token 已配置"
        return "warn", "Discord API 无法连接，请检查网络或代理配置"
