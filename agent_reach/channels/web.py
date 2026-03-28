# -*- coding: utf-8 -*-
"""Web — any URL via Jina Reader. Always available."""

import requests
from urllib.parse import urlparse

from .base import Channel


class WebChannel(Channel):
    name = "web"
    description = "任意网页"
    backends = ["Jina Reader"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        return True  # Fallback — handles any URL

    def check(self, config=None):
        return "ok", "通过 Jina Reader 读取任意网页（curl https://r.jina.ai/URL）"

    def read(self, url: str) -> str:
        """Read a web URL with basic normalization and error handling."""
        if not url:
            return "URL is empty"

        parsed = urlparse(url)
        if not parsed.scheme:
            url = "http://" + url

        headers = {
            "User-Agent": "agent-reach/1.0 (+https://github.com/Panniantong/agent-reach)"
        }

        try:
            resp = requests.get(url, timeout=10, headers=headers)
            resp.raise_for_status()
            text = resp.text.strip()
            if not text:
                return "Empty response body"
            if len(text) > 10000:
                return text[:10000] + "\n... (truncated)"
            return text
        except requests.exceptions.RequestException as exc:
            return f"Error fetching URL {url}: {exc}"
