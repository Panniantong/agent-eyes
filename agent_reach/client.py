# -*- coding: utf-8 -*-
"""Public SDK for external Agent Reach consumers."""

from __future__ import annotations

from typing import Dict, Optional

from agent_reach.adapters import get_adapter
from agent_reach.channels import get_all_channel_contracts
from agent_reach.config import Config
from agent_reach.results import CollectionResult, build_error, build_result


class _Namespace:
    """Thin per-channel SDK namespace."""

    def __init__(self, client: "AgentReachClient", channel: str):
        self._client = client
        self._channel = channel

    def read(self, value: str, limit: int | None = None) -> CollectionResult:
        """Run the standard read operation for this channel."""

        return self._client.collect(self._channel, "read", value, limit=limit)

    def search(self, value: str, limit: int | None = None) -> CollectionResult:
        """Run the standard search operation for this channel."""

        return self._client.collect(self._channel, "search", value, limit=limit)


class AgentReachClient:
    """Public SDK for diagnostics, registry lookups, and read-only collection."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.web = _Namespace(self, "web")
        self.exa = _Namespace(self, "exa_search")
        self.exa_search = self.exa
        self.github = _Namespace(self, "github")
        self.youtube = _Namespace(self, "youtube")
        self.rss = _Namespace(self, "rss")
        self.twitter = _Namespace(self, "twitter")

    def doctor(self) -> Dict[str, dict]:
        from agent_reach.doctor import check_all

        return check_all(self.config)

    def doctor_payload(self, probe: bool = False) -> dict:
        from agent_reach.doctor import check_all, make_doctor_payload

        return make_doctor_payload(check_all(self.config, probe=probe), probe=probe)

    def doctor_report(self) -> str:
        from agent_reach.doctor import check_all, format_report

        return format_report(check_all(self.config))

    def channels(self) -> list[dict]:
        """Return the stable channel registry contract."""

        return get_all_channel_contracts()

    def collect(
        self, channel: str, operation: str, value: str, limit: int | None = None
    ) -> CollectionResult:
        """Run a supported collection operation and return a stable result envelope."""

        text_value = value.strip()
        if not text_value:
            return build_result(
                ok=False,
                channel=channel,
                operation=operation,
                meta={"input": value},
                error=build_error(
                    code="invalid_input",
                    message="Collection input must not be empty",
                    details={},
                ),
            )

        if limit is not None and limit < 1:
            return build_result(
                ok=False,
                channel=channel,
                operation=operation,
                meta={"input": text_value, "limit": limit},
                error=build_error(
                    code="invalid_input",
                    message="limit must be greater than or equal to 1",
                    details={"limit": limit},
                ),
            )

        adapter = get_adapter(channel, config=self.config)
        if adapter is None:
            return build_result(
                ok=False,
                channel=channel,
                operation=operation,
                meta={"input": text_value},
                error=build_error(
                    code="unknown_channel",
                    message=f"Unknown channel: {channel}",
                    details={},
                ),
            )

        if operation not in adapter.supported_operations():
            return build_result(
                ok=False,
                channel=channel,
                operation=operation,
                meta={
                    "input": text_value,
                    "supported_operations": list(adapter.supported_operations()),
                },
                error=build_error(
                    code="unsupported_operation",
                    message=f"{channel} does not support operation: {operation}",
                    details={"supported_operations": list(adapter.supported_operations())},
                ),
            )

        method = getattr(adapter, operation)
        try:
            if limit is None:
                return method(text_value)
            return method(text_value, limit=limit)
        except Exception as exc:
            return build_result(
                ok=False,
                channel=channel,
                operation=operation,
                meta={"input": text_value, **({"limit": limit} if limit is not None else {})},
                error=build_error(
                    code="internal_error",
                    message=f"{channel} {operation} raised an unexpected error: {exc}",
                    details={"exception_type": type(exc).__name__},
                ),
            )


class AgentReach(AgentReachClient):
    """Backward-compatible facade for existing health-check consumers."""
