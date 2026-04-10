# -*- coding: utf-8 -*-
"""Reddit channel checks."""

from __future__ import annotations

from agent_reach.adapters.reddit import RedditAdapter
from agent_reach.utils.commands import find_command

from .base import Channel


class RedditChannel(Channel):
    name = "reddit"
    description = "Reddit search results and public discussion threads"
    backends = ["rdt-cli"]
    tier = 2
    auth_kind = "none"
    entrypoint_kind = "cli"
    operations = ["search", "read"]
    operation_inputs = {
        "search": "query",
        "read": "post",
    }
    required_commands = ["rdt"]
    host_patterns = ["https://www.reddit.com/*", "https://old.reddit.com/*", "https://redd.it/*"]
    example_invocations = [
        'agent-reach collect --channel reddit --operation search --input "r/LocalLLaMA agent frameworks" --limit 10 --json',
        'agent-reach collect --channel reddit --operation read --input "https://www.reddit.com/r/redditdev/comments/..." --limit 20 --json',
    ]
    supports_probe = True
    install_hints = [
        "Install rdt-cli with `uv tool install rdt-cli`.",
        "No Reddit OAuth token, client ID, client secret, or User-Agent configuration is required.",
    ]

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse

        host = urlparse(url).netloc.lower()
        return "reddit.com" in host or "redd.it" in host

    def check(self, config=None):
        if find_command("rdt"):
            return "ok", "rdt-cli is available for no-auth Reddit search/read"
        return "warn", "rdt-cli is missing. Install it with `uv tool install rdt-cli`."

    def probe(self, config=None):
        status, message = self.check(config)
        if status != "ok":
            return status, message

        payload = RedditAdapter(config=config).search("reddit", limit=1)
        if payload["ok"] and payload.get("items"):
            return "ok", "Reddit live rdt-cli search probe succeeded"
        if payload["ok"]:
            return "warn", "Reddit live probe completed but returned zero items"
        error = payload.get("error")
        return "warn", str((error.get("message") if error else None) or "Reddit live probe failed")
