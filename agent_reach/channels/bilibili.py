# -*- coding: utf-8 -*-
"""Bilibili — via yt-dlp (same backend as YouTube).

Backend: yt-dlp (https://github.com/yt-dlp/yt-dlp)
yt-dlp natively supports Bilibili — video info, subtitles, and search.
"""

import json
import shutil
import subprocess
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List


class BilibiliChannel(Channel):
    name = "bilibili"
    description = "B站视频信息和字幕"
    backends = ["yt-dlp"]
    requires_tools = ["yt-dlp"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        d = urlparse(url).netloc.lower()
        return "bilibili.com" in d or "b23.tv" in d

    def check(self, config=None):
        if not shutil.which("yt-dlp"):
            return "off", "yt-dlp 未安装。安装：pip install yt-dlp"
        proxy = config.get("bilibili_proxy") if config else None
        if proxy:
            return "ok", "已配置代理，完整可用"
        import os
        is_server = bool(os.environ.get("SSH_CONNECTION") or os.path.exists("/etc/cloud"))
        if is_server:
            return "warn", "服务器 IP 可能被封，配置代理即可解决：agent-reach configure proxy URL"
        return "ok", "本地直连可用"

    async def read(self, url: str, config=None) -> ReadResult:
        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp not installed. Install: pip install yt-dlp")

        proxy = config.get("bilibili_proxy") if config else None

        # Get video info via yt-dlp
        info = self._get_info(url, proxy)
        if not info:
            return ReadResult(
                title="Bilibili",
                content=f"⚠️ 无法获取视频信息: {url}\n服务器 IP 可能被封，配个代理：agent-reach configure proxy URL",
                url=url, platform="bilibili",
            )

        title = info.get("title", url)
        author = info.get("uploader", "")
        desc = info.get("description", "")

        # Try subtitles
        subtitle = self._get_subtitles(url, proxy)
        content = desc
        if subtitle:
            content += f"\n\n## 字幕\n{subtitle}"

        return ReadResult(
            title=title, content=content, url=url,
            author=author, platform="bilibili",
            extra={
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "duration": info.get("duration_string"),
            },
        )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        """Search Bilibili via yt-dlp's bilisearch."""
        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp not installed. Install: pip install yt-dlp")

        limit = kwargs.get("limit", 10)
        proxy = config.get("bilibili_proxy") if config else None

        cmd = [
            "yt-dlp", "--dump-json", "--flat-playlist",
            f"bilisearch{limit}:{query}",
        ]
        if proxy:
            cmd += ["--proxy", proxy]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            results = []
            for line in r.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    results.append(SearchResult(
                        title=d.get("title", ""),
                        url=f"https://www.bilibili.com/video/{d.get('id', '')}",
                        snippet=f"👤 {d.get('uploader', '?')} · 👁 {d.get('view_count', '?')}",
                        extra={
                            "view_count": d.get("view_count"),
                            "uploader": d.get("uploader"),
                        },
                    ))
                except json.JSONDecodeError:
                    continue
            return results
        except subprocess.TimeoutExpired:
            return []

    def _get_info(self, url: str, proxy: str = None) -> dict:
        cmd = ["yt-dlp", "--dump-json", "--no-download", url]
        if proxy:
            cmd += ["--proxy", proxy]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return json.loads(r.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        return {}

    def _get_subtitles(self, url: str, proxy: str = None) -> str:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "yt-dlp", "--write-sub", "--write-auto-sub",
                "--sub-lang", "zh-Hans,zh,en",
                "--skip-download", "--sub-format", "vtt",
                "-o", f"{tmpdir}/%(id)s.%(ext)s", url,
            ]
            if proxy:
                cmd += ["--proxy", proxy]
            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                for f in Path(tmpdir).glob("*.vtt"):
                    text = f.read_text(errors="replace")
                    lines = []
                    for line in text.split("\n"):
                        line = line.strip()
                        if not line or line.startswith("WEBVTT") or "-->" in line or line.isdigit():
                            continue
                        if line not in lines[-1:]:
                            lines.append(line)
                    return "\n".join(lines)
            except subprocess.TimeoutExpired:
                pass
        return ""
