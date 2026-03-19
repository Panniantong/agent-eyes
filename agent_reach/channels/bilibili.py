# -*- coding: utf-8 -*-
"""Bilibili — video via yt-dlp, search via /x/web-interface API."""

import json
import os
import shutil
import subprocess
import urllib.request
from .base import Channel

_UA = "agent-reach/1.0"
_TIMEOUT = 10
_SEARCH_API = "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=test&page=1"


def _search_api_ok() -> bool:
    """Return True if Bilibili search API responds with code 0."""
    req = urllib.request.Request(_SEARCH_API, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data.get("code") == 0
    except Exception:
        return False


def _bilisearch_ok() -> bool:
    """Return True if yt-dlp bilisearch works without 412."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--no-download", "-j",
             "bilisearch1:test"],
            capture_output=True, text=True, timeout=_TIMEOUT,
        )
        return result.returncode == 0
    except Exception:
        return False


class BilibiliChannel(Channel):
    name = "bilibili"
    description = "B站视频和字幕"
    backends = ["yt-dlp", "B站搜索 API"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "bilibili.com" in d or "b23.tv" in d

    def check(self, config=None):
        if not shutil.which("yt-dlp"):
            return "off", "yt-dlp 未安装。安装：pip install yt-dlp"

        proxy = (config.get("bilibili_proxy") if config else None) or os.environ.get("BILIBILI_PROXY")

        # 检测搜索 API 连通性
        api_ok = _search_api_ok()
        # 检测 yt-dlp bilisearch 是否 412
        ytdlp_search_ok = _bilisearch_ok()

        parts = []

        # 视频读取状态
        if proxy:
            parts.append("视频读取：yt-dlp（代理已配置）")
        else:
            parts.append("视频读取：yt-dlp（本地环境，服务器可能需要代理）")

        # 搜索状态
        if api_ok:
            parts.append("搜索：B站 API 可用（/x/web-interface/search/all/v2）")
        else:
            parts.append("搜索：B站 API 不可达，搜索功能可能受限")

        if not ytdlp_search_ok:
            parts.append("提示：yt-dlp bilisearch 不可用（可能 HTTP 412 反爬），搜索将走 B站 API")

        status = "ok" if api_ok else "warn"
        return status, "。".join(parts)
