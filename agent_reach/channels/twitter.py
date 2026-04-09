# -*- coding: utf-8 -*-
"""Twitter/X channel checks."""

from __future__ import annotations

import os
import shutil
import subprocess

from agent_reach.utils.commands import find_command

from .base import Channel


class TwitterChannel(Channel):
    name = "twitter"
    description = "Twitter/X search and timeline access"
    backends = ["twitter-cli"]
    tier = 1
    auth_kind = "cookie"
    entrypoint_kind = "cli"
    operations = ["search"]
    required_commands = ["twitter"]
    host_patterns = ["https://x.com/*", "https://twitter.com/*"]
    example_invocations = [
        'agent-reach collect --channel twitter --operation search --input "gpt-5.4" --limit 10 --json',
        'twitter status',
    ]
    supports_probe = True
    install_hints = [
        "Install twitter-cli with uv tool install twitter-cli.",
        'Configure cookies with agent-reach configure twitter-cookies "auth_token=...; ct0=...".',
    ]

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse

        host = urlparse(url).netloc.lower()
        return "x.com" in host or "twitter.com" in host

    def check(self, config=None):
        twitter = find_command("twitter") or shutil.which("twitter")
        if not twitter:
            return "warn", "twitter-cli is missing. Install it with uv tool install twitter-cli"

        try:
            result = subprocess.run(
                [twitter, "status"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                env=_twitter_runtime_env(config),
            )
        except Exception:
            return "warn", "twitter-cli is installed but status could not be checked"

        output = f"{result.stdout}\n{result.stderr}".lower()
        if result.returncode == 0 and "ok: true" in output:
            return "ok", "Ready for tweet reads, search, and timeline lookups"
        if "not_authenticated" in output:
            return "warn", (
                "twitter-cli is installed but not authenticated. "
                "Run agent-reach configure twitter-cookies \"auth_token=...; ct0=...\""
            )
        return "warn", "twitter-cli is installed but did not report a healthy session"

    def probe(self, config=None):
        return self.check(config)


def _twitter_runtime_env(config=None) -> dict[str, str]:
    env = os.environ.copy()
    auth_token = env.get("TWITTER_AUTH_TOKEN") or env.get("AUTH_TOKEN")
    ct0 = env.get("TWITTER_CT0") or env.get("CT0")

    if config is not None:
        auth_token = auth_token or config.get("twitter_auth_token")
        ct0 = ct0 or config.get("twitter_ct0")

    if auth_token and ct0:
        env["TWITTER_AUTH_TOKEN"] = str(auth_token)
        env["TWITTER_CT0"] = str(ct0)
        env["AUTH_TOKEN"] = str(auth_token)
        env["CT0"] = str(ct0)
    return env
