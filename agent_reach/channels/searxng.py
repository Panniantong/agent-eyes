# -*- coding: utf-8 -*-
"""SearXNG channel checks."""

from __future__ import annotations

from agent_reach.adapters.searxng import SearXNGAdapter

from .base import Channel


class SearXNGChannel(Channel):
    name = "searxng"
    description = "Configurable metasearch via a SearXNG instance"
    backends = ["SearXNG"]
    auth_kind = "runtime"
    entrypoint_kind = "python"
    operations = ["search"]
    operation_inputs = {"search": "query"}
    host_patterns = []
    example_invocations = [
        'agent-reach configure searxng-base-url "https://searx.example.org"',
        'agent-reach collect --channel searxng --operation search --input "today ai tools" --limit 10 --json',
    ]
    supports_probe = True
    install_hints = [
        "Save a SearXNG instance with agent-reach configure searxng-base-url <INSTANCE_URL>.",
        "Use an instance that enables format=json on /search.",
    ]

    def can_handle(self, url: str) -> bool:
        return False

    def check(self, config=None):
        base_url = config.get("searxng_base_url") if config else None
        if not base_url:
            return (
                "off",
                "SearXNG base URL is not configured. Run agent-reach configure searxng-base-url <INSTANCE_URL>",
            )
        return "ok", f"Configured for SearXNG JSON search at {base_url}"

    def probe(self, config=None):
        status, message = self.check(config)
        if status != "ok":
            return status, message

        payload = SearXNGAdapter(config=config).search("agent reach", limit=1)
        if payload["ok"] and payload.get("items"):
            return "ok", "SearXNG completed a live JSON search probe"
        if payload["ok"]:
            return "warn", "SearXNG probe completed but returned zero items"
        error = payload.get("error")
        if error:
            return "warn", str(error.get("message") or "SearXNG probe failed")
        return "warn", "SearXNG probe failed"
