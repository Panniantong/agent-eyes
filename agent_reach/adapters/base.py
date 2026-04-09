# -*- coding: utf-8 -*-
"""Shared adapter utilities for external collection APIs."""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any

from agent_reach.config import Config
from agent_reach.results import CollectionResult, NormalizedItem, build_error, build_result
from agent_reach.utils.commands import find_command


class BaseAdapter:
    """Base helper for per-channel collection adapters."""

    channel: str = ""
    operations: tuple[str, ...] = ()

    def __init__(self, config: Config | None = None):
        self.config = config or Config()

    def supported_operations(self) -> tuple[str, ...]:
        """Return the operations supported by this adapter."""

        return self.operations

    def error_result(
        self,
        operation: str,
        *,
        code: str,
        message: str,
        raw: Any = None,
        meta: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> CollectionResult:
        """Build an error result envelope."""

        return build_result(
            ok=False,
            channel=self.channel,
            operation=operation,
            raw=raw,
            meta=meta,
            error=build_error(code=code, message=message, details=details),
        )

    def ok_result(
        self,
        operation: str,
        *,
        items: list[NormalizedItem],
        raw: Any,
        meta: dict[str, Any] | None = None,
    ) -> CollectionResult:
        """Build a success result envelope."""

        return build_result(
            ok=True,
            channel=self.channel,
            operation=operation,
            items=items,
            raw=raw,
            meta=meta,
            error=None,
        )

    def make_meta(
        self,
        *,
        value: str,
        limit: int | None = None,
        started_at: float | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Build common metadata for adapter results."""

        meta: dict[str, Any] = {
            "input": value,
        }
        if limit is not None:
            meta["limit"] = limit
        if started_at is not None:
            meta["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
        meta.update(extra)
        return meta

    def runtime_env(self) -> dict[str, str]:
        """Return the non-interactive runtime environment for backend commands."""

        env = os.environ.copy()
        github_token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN") or self.config.get("github_token")
        if github_token:
            env["GITHUB_TOKEN"] = str(github_token)
            env["GH_TOKEN"] = str(github_token)

        twitter_auth = env.get("TWITTER_AUTH_TOKEN") or env.get("AUTH_TOKEN") or self.config.get("twitter_auth_token")
        twitter_ct0 = env.get("TWITTER_CT0") or env.get("CT0") or self.config.get("twitter_ct0")
        if twitter_auth and twitter_ct0:
            env["TWITTER_AUTH_TOKEN"] = str(twitter_auth)
            env["TWITTER_CT0"] = str(twitter_ct0)
            env["AUTH_TOKEN"] = str(twitter_auth)
            env["CT0"] = str(twitter_ct0)
        return env

    def command_path(self, name: str) -> str | None:
        """Resolve a runtime command path."""

        return find_command(name)

    def run_command(
        self,
        command: list[str],
        *,
        timeout: int = 120,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Run a backend command in non-interactive mode."""

        return subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env or self.runtime_env(),
        )
