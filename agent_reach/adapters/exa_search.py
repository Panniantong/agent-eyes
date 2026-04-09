# -*- coding: utf-8 -*-
"""Exa search collection adapter."""

from __future__ import annotations

import json
import re
import time

from agent_reach.results import CollectionResult, NormalizedItem, build_item, parse_timestamp
from agent_reach.utils.paths import get_mcporter_config_path

from .base import BaseAdapter

_ENTRY_RE = re.compile(
    r"Title:\s*(?P<title>.*?)\n"
    r"URL:\s*(?P<url>.*?)\n"
    r"Published:\s*(?P<published>.*?)\n"
    r"Author:\s*(?P<author>.*?)\n"
    r"Highlights:\n(?P<highlights>.*?)(?=(?:\nTitle: )|\Z)",
    re.DOTALL,
)


def _parse_text_results(text: str) -> list[NormalizedItem]:
    items: list[NormalizedItem] = []
    for match in _ENTRY_RE.finditer(text.strip()):
        title = match.group("title").strip() or None
        url = match.group("url").strip() or None
        published = match.group("published").strip()
        author = match.group("author").strip()
        highlights = match.group("highlights").strip()
        item = build_item(
            item_id=url or title or f"exa-{len(items)}",
            kind="search_result",
            title=title,
            url=url,
            text=highlights,
            author=None if author == "N/A" else author,
            published_at=None if published == "N/A" else parse_timestamp(published),
            source="exa_search",
            extras={"highlights": highlights},
        )
        items.append(item)
    return items


class ExaSearchAdapter(BaseAdapter):
    """Search the web through Exa MCP."""

    channel = "exa_search"
    operations = ("search",)

    def search(self, query: str, limit: int = 5) -> CollectionResult:
        started_at = time.perf_counter()
        mcporter = self.command_path("mcporter")
        if not mcporter:
            return self.error_result(
                "search",
                code="missing_dependency",
                message="mcporter is missing. Install it with npm install -g mcporter",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        payload = json.dumps({"query": query, "numResults": limit}, ensure_ascii=False)
        try:
            result = self.run_command(
                [
                    mcporter,
                    "--config",
                    str(get_mcporter_config_path()),
                    "call",
                    "exa.web_search_exa",
                    "--args",
                    payload,
                    "--output",
                    "json",
                ],
                timeout=120,
            )
        except Exception as exc:
            return self.error_result(
                "search",
                code="command_failed",
                message=f"Exa search failed: {exc}",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        raw_output = f"{result.stdout}\n{result.stderr}".strip()
        if result.returncode != 0:
            return self.error_result(
                "search",
                code="command_failed",
                message="Exa search command did not complete cleanly",
                raw=raw_output,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
                details={"returncode": result.returncode},
            )

        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError:
            return self.error_result(
                "search",
                code="invalid_response",
                message="Exa returned a non-JSON payload",
                raw=raw_output,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        text_blocks = [
            block.get("text", "")
            for block in raw.get("content", [])
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        items: list[NormalizedItem] = []
        for block in text_blocks:
            items.extend(_parse_text_results(block))

        if text_blocks and not items:
            return self.error_result(
                "search",
                code="invalid_response",
                message="Exa returned a payload that could not be normalized",
                raw=raw,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        return self.ok_result(
            "search",
            items=items,
            raw=raw,
            meta=self.make_meta(value=query, limit=limit, started_at=started_at),
        )
