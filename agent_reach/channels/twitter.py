# -*- coding: utf-8 -*-
"""Twitter/X channel checks."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from agent_reach.adapters.twitter import TwitterAdapter
from agent_reach.results import CollectionError, CollectionResult
from agent_reach.utils.commands import find_command

from .base import Channel

PROBE_USER = "openai"
PROBE_SEARCH_QUERY = "OpenAI"


class TwitterChannel(Channel):
    name = "twitter"
    description = "Twitter/X search, profiles, posts, and tweet threads"
    backends = ["twitter-cli"]
    tier = 1
    auth_kind = "cookie"
    entrypoint_kind = "cli"
    operations = ["search", "user", "user_posts", "tweet"]
    required_commands = ["twitter"]
    host_patterns = ["https://x.com/*", "https://twitter.com/*"]
    example_invocations = [
        'agent-reach collect --channel twitter --operation search --input "gpt-5.4" --limit 10 --json',
        'agent-reach collect --channel twitter --operation user --input "openai" --json',
        'agent-reach collect --channel twitter --operation user_posts --input "openai" --limit 20 --json',
        'agent-reach collect --channel twitter --operation tweet --input "https://x.com/OpenAI/status/2042296046009626989" --limit 20 --json',
        'twitter status',
    ]
    supports_probe = True
    install_hints = [
        "Install twitter-cli with uv tool install twitter-cli.",
        'Configure cookies with agent-reach configure twitter-cookies "auth_token=...; ct0=...".',
    ]

    def _all_operation_statuses(self, status: str, message: str) -> dict[str, dict[str, str]]:
        return {operation: {"status": status, "message": message} for operation in self.operations}

    def _operation_status_from_result(
        self,
        payload: CollectionResult,
        *,
        success_message: str,
        empty_message: str | None = None,
    ) -> dict[str, Any]:
        if payload.get("ok"):
            count = len(payload.get("items") or [])
            if count or empty_message is None:
                return {
                    "status": "ok",
                    "message": success_message,
                    "count": count,
                }
            return {
                "status": "warn",
                "message": empty_message,
                "count": count,
            }

        error: CollectionError = payload.get("error") or {
            "code": "command_failed",
            "message": "operation failed",
            "details": {},
        }
        return {
            "status": "warn",
            "message": error.get("message") or "operation failed",
            "error_code": error.get("code") or "command_failed",
            "details": error.get("details") or {},
        }

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse

        host = urlparse(url).netloc.lower()
        return "x.com" in host or "twitter.com" in host

    def check(self, config=None):
        twitter = find_command("twitter") or shutil.which("twitter")
        if not twitter:
            return "warn", "twitter-cli is missing. Install it with uv tool install twitter-cli", {
                "diagnostic_basis": "command_lookup",
                "operation_statuses": self._all_operation_statuses(
                    "off",
                    "twitter-cli is missing. Install it with uv tool install twitter-cli",
                ),
            }

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
            return "warn", "twitter-cli is installed but status could not be checked", {
                "diagnostic_basis": "twitter status",
                "operation_statuses": self._all_operation_statuses(
                    "unknown",
                    "twitter-cli status could not be checked. Run agent-reach doctor --json --probe.",
                ),
            }

        output = f"{result.stdout}\n{result.stderr}".lower()
        if result.returncode == 0 and "ok: true" in output:
            return (
                "warn",
                "twitter-cli session is authenticated, but live Twitter operations are not verified until agent-reach doctor --json --probe",
                {
                    "diagnostic_basis": "twitter status",
                    "operation_statuses": self._all_operation_statuses(
                        "unknown",
                        "Not verified by twitter status alone. Run agent-reach doctor --json --probe.",
                    ),
                },
            )
        if "not_authenticated" in output:
            return (
                "warn",
                "twitter-cli is installed but not authenticated. "
                "Run agent-reach configure twitter-cookies \"auth_token=...; ct0=...\"",
                {
                    "diagnostic_basis": "twitter status",
                    "operation_statuses": self._all_operation_statuses(
                        "off",
                        "Authentication is required. Run agent-reach configure twitter-cookies \"auth_token=...; ct0=...\"",
                    ),
                },
            )
        return "warn", "twitter-cli is installed but did not report a healthy session", {
            "diagnostic_basis": "twitter status",
            "operation_statuses": self._all_operation_statuses(
                "unknown",
                "twitter-cli did not report a healthy session. Run agent-reach doctor --json --probe.",
            ),
        }

    def probe(self, config=None):
        twitter = find_command("twitter") or shutil.which("twitter")
        if not twitter:
            return "warn", "twitter-cli is missing. Install it with uv tool install twitter-cli", {
                "probed_operations": [],
                "probe_inputs": {},
                "operation_statuses": self._all_operation_statuses(
                    "off",
                    "twitter-cli is missing. Install it with uv tool install twitter-cli",
                ),
            }

        adapter = TwitterAdapter(config=config)
        try:
            user_payload = adapter.user(PROBE_USER)
            search_payload = adapter.search(PROBE_SEARCH_QUERY, limit=1)
        except Exception as exc:
            return "warn", f"twitter-cli is installed but the live Twitter probes crashed: {exc}", {
                "probed_operations": ["user", "search"],
                "probe_inputs": {
                    "user": PROBE_USER,
                    "search": PROBE_SEARCH_QUERY,
                },
            }

        operation_statuses = self._all_operation_statuses(
            "unknown",
            "Not probed by agent-reach doctor --json --probe.",
        )
        operation_statuses["user"] = self._operation_status_from_result(
            user_payload,
            success_message="Live user lookup succeeded via twitter-cli",
        )
        operation_statuses["search"] = self._operation_status_from_result(
            search_payload,
            success_message="Live search succeeded via twitter-cli",
            empty_message="Live search completed but returned zero items for the probe query",
        )

        if user_payload["ok"] and search_payload["ok"] and search_payload.get("items"):
            return "ok", "Live user lookup and search both succeeded via twitter-cli", {
                "probed_operations": ["user", "search"],
                "probe_inputs": {
                    "user": PROBE_USER,
                    "search": PROBE_SEARCH_QUERY,
                },
                "operation_statuses": operation_statuses,
            }

        user_error: CollectionError = user_payload.get("error") or {
            "code": "",
            "message": "",
            "details": {},
        }
        search_error: CollectionError = search_payload.get("error") or {
            "code": "",
            "message": "",
            "details": {},
        }
        user_code = user_error.get("code") or ""
        search_code = search_error.get("code") or ""
        if user_code == "not_authenticated" and search_code in {"", "not_authenticated"}:
            return "warn", (
                "twitter-cli is installed but live Twitter probes are not authenticated. "
                "Run agent-reach configure twitter-cookies \"auth_token=...; ct0=...\""
            ), {
                "probed_operations": ["user", "search"],
                "probe_inputs": {
                    "user": PROBE_USER,
                    "search": PROBE_SEARCH_QUERY,
                },
                "operation_statuses": operation_statuses,
            }

        if user_payload["ok"] and not search_payload["ok"]:
            return "warn", (
                "Live user lookup succeeded, but live search failed "
                f"({search_code or 'command_failed'}): {search_error.get('message') or 'search failed'}"
            ), {
                "probed_operations": ["user", "search"],
                "probe_inputs": {
                    "user": PROBE_USER,
                    "search": PROBE_SEARCH_QUERY,
                },
                "operation_statuses": operation_statuses,
            }

        if search_payload["ok"] and not user_payload["ok"]:
            return "warn", (
                "Live search succeeded, but live user lookup failed "
                f"({user_code or 'command_failed'}): {user_error.get('message') or 'user lookup failed'}"
            ), {
                "probed_operations": ["user", "search"],
                "probe_inputs": {
                    "user": PROBE_USER,
                    "search": PROBE_SEARCH_QUERY,
                },
                "operation_statuses": operation_statuses,
            }

        return "warn", (
            "twitter-cli is installed but live user lookup and search both failed. "
            f"user={user_code or 'command_failed'}, search={search_code or 'command_failed'}"
        ), {
            "probed_operations": ["user", "search"],
            "probe_inputs": {
                "user": PROBE_USER,
                "search": PROBE_SEARCH_QUERY,
            },
            "operation_statuses": operation_statuses,
        }


def _twitter_runtime_env(config=None) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
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
