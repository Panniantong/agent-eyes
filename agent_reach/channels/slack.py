# -*- coding: utf-8 -*-
"""Slack — check connectivity and configuration."""

import os
import urllib.request
from .base import Channel

_TIMEOUT = 10


def _slack_reachable() -> bool:
    """Return True if Slack API is reachable."""
    url = "https://slack.com/api/api.test"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False


class SlackChannel(Channel):
    name = "slack"
    description = "Slack 工作区消息和频道"
    backends = ["Slack API"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "slack.com" in d

    def check(self, config=None):
        token = (config.get("slack_token") if config else None) or os.environ.get("SLACK_TOKEN")
        if not token:
            return "warn", (
                "未配置 Slack Token。请设置环境变量：\n"
                "  export SLACK_TOKEN=xoxb-your-token"
            )
        if _slack_reachable():
            return "ok", "Slack API 可达，Token 已配置"
        return "warn", "Slack API 无法连接，请检查网络或代理配置"
