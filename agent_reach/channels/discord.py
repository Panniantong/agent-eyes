# -*- coding: utf-8 -*-
"""Discord channel — search via Exa, read public server info via Invite API."""

import json
import shutil
import subprocess
import urllib.request
from typing import Tuple

from .base import Channel

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
_INVITE_API = "https://discord.com/api/v10/invites/{code}?with_counts=true"


def _exa_available() -> bool:
    mcporter = shutil.which("mcporter")
    if not mcporter:
        return False
    try:
        r = subprocess.run(
            [mcporter, "config", "list"],
            capture_output=True, text=True, timeout=5
        )
        return "exa" in r.stdout.lower()
    except Exception:
        return False


def _get_invite_code(url: str) -> str:
    """Extract invite code from discord.gg/xxx or discord.com/invite/xxx URLs."""
    url = url.rstrip("/")
    for prefix in ("discord.gg/", "discord.com/invite/"):
        if prefix in url:
            return url.split(prefix)[-1].split("/")[0].split("?")[0]
    return ""


class DiscordChannel(Channel):
    name = "discord"
    description = "Discord 服务器信息与内容搜索"
    backends = ["Exa via mcporter (搜索)", "Discord Invite API (服务器信息)"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        return "discord.gg" in url or "discord.com" in url

    def check(self, config=None) -> Tuple[str, str]:
        if _exa_available():
            return "ok", "Discord 可用：Exa 搜索内容，Invite API 读取公开服务器信息"
        return "warn", (
            "Discord Invite API 可用（无需配置），但搜索功能需要 mcporter + Exa MCP。"
            "运行 `agent-reach install --env=auto` 安装 Exa。"
        )

    def read(self, url: str) -> str:
        """读取 Discord 服务器公开信息（Invite API）或通过 Jina 读取页面。"""
        code = _get_invite_code(url)
        if code:
            api_url = _INVITE_API.format(code=code)
            req = urllib.request.Request(api_url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            guild = data.get("guild", {})
            channel = data.get("channel", {})
            members = data.get("approximate_member_count", "未知")
            online = data.get("approximate_presence_count", "未知")
            return (
                f"# {guild.get('name', '未知服务器')}\n\n"
                f"**描述**: {guild.get('description') or '无'}\n"
                f"**成员**: {members:,} 人（在线 {online:,}）\n"
                f"**频道**: #{channel.get('name', '未知')}\n"
                f"**邀请链接**: {url}\n"
            )
        # Fallback: Jina Reader
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        jina_url = f"https://r.jina.ai/{url}"
        req = urllib.request.Request(
            jina_url, headers={"User-Agent": _UA, "Accept": "text/plain"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")

    def search(self, query: str, limit: int = 5) -> str:
        """通过 Exa 搜索 Discord 内容（服务器、帖子、讨论）。"""
        mcporter = shutil.which("mcporter")
        if not mcporter:
            return "搜索需要 mcporter，请运行 `npm install -g mcporter` 安装。"
        cmd = (
            f"mcporter call 'exa.web_search_exa("
            f"query: \"{query} site:discord.com OR site:discord.gg\", "
            f"numResults: {limit}, "
            f"includeDomains: [\"discord.com\", \"discord.gg\"])'"
        )
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout or r.stderr
