# -*- coding: utf-8 -*-
"""Twitter/X collection adapter."""

from __future__ import annotations

import json
import time

from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    derive_title_from_text,
    parse_timestamp,
)

from .base import BaseAdapter


class TwitterAdapter(BaseAdapter):
    """Search tweets through twitter-cli."""

    channel = "twitter"
    operations = ("search",)

    def search(self, query: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        twitter = self.command_path("twitter")
        if not twitter:
            return self.error_result(
                "search",
                code="missing_dependency",
                message="twitter-cli is missing. Install it with uv tool install twitter-cli",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        try:
            result = self.run_command(
                [
                    twitter,
                    "search",
                    query,
                    "-n",
                    str(limit),
                    "--json",
                ],
                timeout=120,
            )
        except Exception as exc:
            return self.error_result(
                "search",
                code="command_failed",
                message=f"Twitter search failed: {exc}",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        raw_output = f"{result.stdout}\n{result.stderr}".strip()
        if result.returncode != 0:
            code = "command_failed"
            if "not_authenticated" in raw_output.lower():
                code = "not_authenticated"
            return self.error_result(
                "search",
                code=code,
                message="Twitter search command did not complete cleanly",
                raw=raw_output,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
                details={"returncode": result.returncode},
            )

        try:
            raw = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return self.error_result(
                "search",
                code="invalid_response",
                message="Twitter search returned a non-JSON payload",
                raw=raw_output,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )
        data = raw.get("data", [])
        items: list[NormalizedItem] = [
            build_item(
                item_id=str(tweet.get("id") or f"tweet-{idx}"),
                kind="post",
                title=derive_title_from_text(tweet.get("text"), fallback=f"Tweet {tweet.get('id')}"),
                url=f"https://x.com/{(tweet.get('author') or {}).get('screenName', 'i')}/status/{tweet.get('id')}" if tweet.get("id") else None,
                text=tweet.get("text"),
                author=(tweet.get("author") or {}).get("screenName"),
                published_at=parse_timestamp(tweet.get("createdAtISO") or tweet.get("createdAt")),
                source=self.channel,
                extras={
                    "author_name": (tweet.get("author") or {}).get("name"),
                    "verified": (tweet.get("author") or {}).get("verified"),
                    "metrics": tweet.get("metrics") or {},
                    "urls": tweet.get("urls") or [],
                    "media": tweet.get("media") or [],
                    "lang": tweet.get("lang"),
                },
            )
            for idx, tweet in enumerate(data)
        ]
        return self.ok_result(
            "search",
            items=items,
            raw=raw,
            meta=self.make_meta(value=query, limit=limit, started_at=started_at),
        )
