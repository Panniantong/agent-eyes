# -*- coding: utf-8 -*-
"""Generic web reading through Jina Reader."""

from __future__ import annotations

import urllib.request

from .base import Channel

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class WebChannel(Channel):
    name = "web"
    description = "Any web page"
    backends = ["Jina Reader"]
    tier = 0
    auth_kind = "none"
    entrypoint_kind = "http_reader"
    operations = ["read"]
    host_patterns = ["http://*", "https://*"]
    example_invocations = [
        'agent-reach collect --channel web --operation read --input "https://example.com" --json',
    ]
    supports_probe = True
    install_hints = [
        "Jina Reader is hosted remotely, so no local binary is required.",
    ]

    def can_handle(self, url: str) -> bool:
        return True

    def check(self, config=None):
        return "ok", "Reads arbitrary pages via https://r.jina.ai/"

    def probe(self, config=None):
        req = urllib.request.Request(
            "https://r.jina.ai/http://example.com",
            headers={"User-Agent": _UA, "Accept": "text/plain"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read(256).decode("utf-8", errors="replace")
        except Exception as exc:
            return "warn", f"Jina Reader probe failed: {exc}"

        if body.strip():
            return "ok", "Jina Reader responded to a live page probe"
        return "warn", "Jina Reader probe returned an empty response"

    def read(self, url: str) -> str:
        """Read a URL as markdown through Jina Reader."""

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        req = urllib.request.Request(
            f"https://r.jina.ai/{url}",
            headers={"User-Agent": _UA, "Accept": "text/plain"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
