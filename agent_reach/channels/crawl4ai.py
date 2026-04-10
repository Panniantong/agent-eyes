# -*- coding: utf-8 -*-
"""crawl4ai channel checks."""

from __future__ import annotations

from urllib.parse import urlparse

from agent_reach.adapters.crawl4ai import _import_crawl4ai

from .base import Channel


class Crawl4AIChannel(Channel):
    name = "crawl4ai"
    description = "Browser-backed page reads and bounded same-origin crawls"
    backends = ["crawl4ai", "Playwright"]
    tier = 2
    auth_kind = "runtime"
    entrypoint_kind = "python"
    operations = ["read", "crawl"]
    operation_inputs = {
        "read": "url",
        "crawl": "url",
    }
    operation_options = {
        "crawl": [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "cli_flag": "--query",
                "sdk_kwarg": "crawl_query",
                "description": "Adaptive crawl goal forwarded to crawl4ai for bounded same-origin exploration.",
            }
        ]
    }
    host_patterns = ["http://*", "https://*"]
    example_invocations = [
        'agent-reach collect --channel crawl4ai --operation read --input "https://example.com" --json',
        'agent-reach collect --channel crawl4ai --operation crawl --input "https://example.com" --query "pricing and faq" --limit 10 --json',
    ]
    supports_probe = False
    install_hints = [
        "Install agent-reach[crawl4ai] into the project environment that needs browser-backed reads.",
        "Install a browser runtime with python -m playwright install chromium.",
        "For checkout development, use uv pip install -e .[crawl4ai].",
    ]

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def check(self, config=None):
        try:
            _import_crawl4ai()
        except ImportError:
            return (
                "off",
                "crawl4ai is not installed. Install agent-reach[crawl4ai] into the environment that needs browser-backed reads, then run python -m playwright install chromium.",
            )
        return "ok", "crawl4ai Python package is available; browser runtime is validated at collection time"
