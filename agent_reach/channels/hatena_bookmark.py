# -*- coding: utf-8 -*-
"""Hatena Bookmark channel checks."""

from __future__ import annotations

import warnings

from .base import Channel


class HatenaBookmarkChannel(Channel):
    name = "hatena_bookmark"
    description = "Hatena Bookmark URL reactions and related entries"
    backends = ["Hatena Bookmark entry API"]
    auth_kind = "none"
    entrypoint_kind = "python"
    operations = ["read"]
    operation_inputs = {"read": "url"}
    host_patterns = [
        "http://*",
        "https://*",
        "https://b.hatena.ne.jp/entry/*",
        "https://bookmark.hatenaapis.com/*",
    ]
    example_invocations = [
        'agent-reach collect --channel hatena_bookmark --operation read --input "https://example.com" --limit 5 --json',
    ]
    supports_probe = True
    install_hints = [
        "Uses Hatena Bookmark's public entry and count APIs over HTTPS.",
    ]

    def can_handle(self, url: str) -> bool:
        return url.startswith(("http://", "https://"))

    def check(self, config=None):
        if not _has_requests():
            return "off", "requests is missing. Install it with pip install requests"
        return "ok", "Ready for Hatena Bookmark URL lookups"

    def probe(self, config=None):
        from agent_reach.adapters.hatena_bookmark import HatenaBookmarkAdapter

        payload = HatenaBookmarkAdapter(config=config).read("https://example.com", limit=2)
        if payload["ok"]:
            return "ok", "Hatena Bookmark completed a live URL lookup"
        return "warn", payload["error"]["message"] if payload["error"] else "Hatena probe failed"


def _has_requests() -> bool:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        try:
            import requests  # noqa: F401
        except ImportError:
            return False
    return True
