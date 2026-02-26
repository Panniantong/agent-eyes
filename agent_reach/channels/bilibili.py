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
        """Search Bilibili.

        Strategy:
        1. Try yt-dlp bilisearch (works on local machines)
        2. Fallback to Exa site:bilibili.com (works on servers)
        """
        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp not installed. Install: pip install yt-dlp")

        limit = kwargs.get("limit", 5)
        proxy = config.get("bilibili_proxy") if config else None

        # Strategy 1: yt-dlp bilisearch
        results = self._search_ytdlp(query, limit, proxy)
        if results:
            return results

        # Strategy 2: Exa fallback (server-friendly)
        results = self._search_exa(query, limit)
        if results:
            return results

        return []

    def _search_ytdlp(self, query: str, limit: int, proxy: str = None) -> List[SearchResult]:
        """Search via yt-dlp bilisearch (needs local/Chinese IP)."""
        cmd = [
            "yt-dlp", "--dump-json", "--no-download",
            f"bilisearch{limit}:{query}",
        ]
        if proxy:
            cmd += ["--proxy", proxy]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                return []
            results = []
            for line in r.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    vid = d.get("id", "")
                    url = d.get("webpage_url", f"https://www.bilibili.com/video/av{vid}")
                    results.append(SearchResult(
                        title=d.get("title", f"av{vid}"),
                        url=url,
                        snippet=f"👤 {d.get('uploader', '?')} · 👁 {d.get('view_count', '?')}",
                        extra={
                            "view_count": d.get("view_count"),
                            "uploader": d.get("uploader"),
                            "duration": d.get("duration_string"),
                        },
                    ))
                except json.JSONDecodeError:
                    continue
            return results
        except subprocess.TimeoutExpired:
            return []

    def _search_exa(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback: search via Exa (site:bilibili.com). Works on any IP."""
        try:
            r = subprocess.run(
                ["mcporter", "call",
                 f'exa.web_search_exa(query: "site:bilibili.com {query}", numResults: {limit})'],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                return []

            results = []
            # Parse mcporter output: Title: / Author: / URL: / Text: blocks
            title, author, url = "", "", ""
            for line in r.stdout.split("\n"):
                if line.startswith("Title: "):
                    title = line[7:].strip()
                elif line.startswith("Author: "):
                    author = line[8:].strip()
                elif line.startswith("URL: "):
                    url = line[5:].strip()
                    if url and "bilibili.com" in url:
                        results.append(SearchResult(
                            title=title or url,
                            url=url,
                            snippet=f"👤 {author}" if author else "(via Exa search)",
                        ))
                    title, author, url = "", "", ""
            return results
        except Exception:
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
