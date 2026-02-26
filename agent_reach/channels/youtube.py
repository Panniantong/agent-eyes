# -*- coding: utf-8 -*-
"""YouTube — via yt-dlp (video info, subtitles, and search).

Backend: yt-dlp (https://github.com/yt-dlp/yt-dlp)
Supports: read (info + subtitles), search (ytsearch)
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List


class YouTubeChannel(Channel):
    name = "youtube"
    description = "YouTube 视频字幕"
    backends = ["yt-dlp"]
    requires_tools = ["yt-dlp"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        d = urlparse(url).netloc.lower()
        return "youtube.com" in d or "youtu.be" in d

    async def read(self, url: str, config=None) -> ReadResult:
        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp not installed. Install: pip install yt-dlp")

        with tempfile.TemporaryDirectory() as tmpdir:
            info = self._get_info(url)
            title = info.get("title", url)
            author = info.get("uploader", "")

            transcript = self._get_subtitles(url, tmpdir)
            if not transcript:
                transcript = f"[Video: {title}]\n[No subtitles available.]"

            return ReadResult(
                title=title, content=transcript, url=url,
                author=author, platform="youtube",
                extra={
                    "duration": info.get("duration_string"),
                    "view_count": info.get("view_count"),
                    "upload_date": info.get("upload_date"),
                },
            )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        """Search YouTube via yt-dlp's ytsearch."""
        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp not installed. Install: pip install yt-dlp")

        limit = kwargs.get("limit", 10)

        try:
            r = subprocess.run(
                ["yt-dlp", "--dump-json", "--flat-playlist",
                 f"ytsearch{limit}:{query}"],
                capture_output=True, text=True, timeout=30,
            )
            results = []
            for line in r.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    vid = d.get("id", "")
                    results.append(SearchResult(
                        title=d.get("title", ""),
                        url=f"https://youtube.com/watch?v={vid}" if vid else "",
                        snippet=(
                            f"👤 {d.get('channel', '?')} · "
                            f"⏱ {d.get('duration_string', '?')} · "
                            f"👁 {d.get('view_count', '?')}"
                        ),
                        extra={
                            "channel": d.get("channel"),
                            "duration": d.get("duration_string"),
                            "view_count": d.get("view_count"),
                        },
                    ))
                except json.JSONDecodeError:
                    continue
            return results
        except subprocess.TimeoutExpired:
            return []

    def _get_info(self, url: str) -> dict:
        try:
            r = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", url],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                return json.loads(r.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        return {}

    def _get_subtitles(self, url: str, tmpdir: str) -> str:
        try:
            subprocess.run(
                ["yt-dlp", "--write-auto-sub", "--write-sub",
                 "--sub-lang", "en,zh-Hans,zh",
                 "--skip-download", "--sub-format", "vtt",
                 "-o", f"{tmpdir}/%(id)s.%(ext)s", url],
                capture_output=True, text=True, timeout=30,
            )
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
