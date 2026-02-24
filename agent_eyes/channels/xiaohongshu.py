# -*- coding: utf-8 -*-
"""XiaoHongShu (小红书) — via cookie-based API access.

Backend: XHS web API + cookies
Swap to: any XHS access method
"""

import re
import json
import requests
from urllib.parse import urlparse
from .base import Channel, ReadResult


class XiaoHongShuChannel(Channel):
    name = "xiaohongshu"
    description = "小红书笔记"
    backends = ["XHS Web API"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "xiaohongshu.com" in domain or "xhslink.com" in domain

    def check(self, config=None):
        cookie = config.get("xhs_cookie") if config else None
        if cookie:
            return "ok", "Cookie 已配置，完整可用"
        return "off", "需要配置 Cookie 才能访问。导入浏览器 Cookie 即可：agent-eyes configure --from-browser chrome"

    async def read(self, url: str, config=None) -> ReadResult:
        cookie = config.get("xhs_cookie") if config else None

        if not cookie:
            return ReadResult(
                title="XiaoHongShu",
                content="⚠️ XiaoHongShu requires cookies to access.\n"
                        "Set up: agent-eyes configure xhs-cookie \"YOUR_COOKIE_STRING\"\n"
                        "How to get it: install Cookie-Editor extension → go to xiaohongshu.com → Export → Header String",
                url=url,
                platform="xiaohongshu",
            )

        # Extract note ID from URL
        note_id = self._extract_note_id(url)
        if not note_id:
            from agent_eyes.channels.web import WebChannel
            return await WebChannel().read(url, config)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Cookie": cookie,
            "Referer": "https://www.xiaohongshu.com/",
        }

        # Fetch note page
        resp = requests.get(
            f"https://www.xiaohongshu.com/explore/{note_id}",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        html = resp.text

        # Extract note data from HTML
        title, content, author = self._parse_html(html)

        return ReadResult(
            title=title or f"XHS Note {note_id}",
            content=content or "Could not extract content. Cookie may be expired.",
            url=url,
            author=author,
            platform="xiaohongshu",
        )

    def _extract_note_id(self, url: str) -> str:
        """Extract note ID from various XHS URL formats."""
        # https://www.xiaohongshu.com/explore/xxxxx
        # https://www.xiaohongshu.com/discovery/item/xxxxx
        # https://xhslink.com/xxxxx
        path = urlparse(url).path
        parts = path.strip("/").split("/")
        if parts:
            return parts[-1]
        return ""

    def _parse_html(self, html: str):
        """Extract title, content, author from XHS HTML."""
        title = ""
        content = ""
        author = ""

        # Try to find JSON data in page
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
        if match:
            try:
                # XHS embeds note data in initial state
                state = json.loads(match.group(1).replace('undefined', 'null'))
                note_data = state.get("note", {}).get("noteDetailMap", {})
                if note_data:
                    first_note = list(note_data.values())[0]
                    note = first_note.get("note", {})
                    title = note.get("title", "")
                    content = note.get("desc", "")
                    author = note.get("user", {}).get("nickname", "")
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        # Fallback: extract from meta tags
        if not title:
            m = re.search(r'<title>(.*?)</title>', html)
            if m:
                title = m.group(1)

        if not content:
            m = re.search(r'<meta name="description" content="(.*?)"', html)
            if m:
                content = m.group(1)

        return title, content, author
