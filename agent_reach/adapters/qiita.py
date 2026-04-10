# -*- coding: utf-8 -*-
"""Qiita collection adapter."""

from __future__ import annotations

import time
import warnings

from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    build_pagination_meta,
    parse_timestamp,
)
from agent_reach.source_hints import article_source_hints

from .base import BaseAdapter

_UA = "agent-reach/1.4.0 (+https://github.com/iwachacha/Agent-Reach)"
_ITEMS_API = "https://qiita.com/api/v2/items"
_BODY_SNIPPET_CHARS = 500
_BODY_MODES = {"none", "snippet", "full"}


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


class QiitaAdapter(BaseAdapter):
    """Search public Qiita items through Qiita API v2."""

    channel = "qiita"
    operations = ("search",)

    def search(self, query: str, limit: int = 10, body_mode: str = "full") -> CollectionResult:
        started_at = time.perf_counter()
        if body_mode not in _BODY_MODES:
            return self.error_result(
                "search",
                code="invalid_input",
                message="body_mode must be one of: none, snippet, full",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at, body_mode=body_mode),
            )

        requests = _import_requests()
        headers = {
            "User-Agent": _UA,
            "Accept": "application/json",
        }
        qiita_token = self.runtime_env().get("QIITA_TOKEN")
        if qiita_token:
            headers["Authorization"] = f"Bearer {qiita_token}"

        try:
            response = requests.get(
                _ITEMS_API,
                params={
                    "query": query,
                    "page": "1",
                    "per_page": str(min(max(limit, 1), 100)),
                },
                headers=headers,
                timeout=30,
            )
        except requests.RequestException as exc:
            return self.error_result(
                "search",
                code="http_error",
                message=f"Qiita search failed: {exc}",
                meta=self.make_meta(
                    value=query,
                    limit=limit,
                    started_at=started_at,
                    body_mode=body_mode,
                ),
            )

        if response.status_code >= 400:
            return self.error_result(
                "search",
                code="http_error",
                message=f"Qiita search returned HTTP {response.status_code}",
                raw=response.text,
                meta=self.make_meta(
                    value=query,
                    limit=limit,
                    started_at=started_at,
                    total_count=response.headers.get("Total-Count"),
                    body_mode=body_mode,
                ),
            )

        try:
            raw = response.json()
        except ValueError:
            return self.error_result(
                "search",
                code="invalid_response",
                message="Qiita search returned a non-JSON payload",
                raw=response.text,
                meta=self.make_meta(
                    value=query,
                    limit=limit,
                    started_at=started_at,
                    body_mode=body_mode,
                ),
            )

        if not isinstance(raw, list):
            return self.error_result(
                "search",
                code="invalid_response",
                message="Qiita search payload was not a list",
                raw=raw,
                meta=self.make_meta(
                    value=query,
                    limit=limit,
                    started_at=started_at,
                    body_mode=body_mode,
                ),
            )

        items: list[NormalizedItem] = []
        for idx, entry in enumerate(raw):
            published_at = parse_timestamp(entry.get("created_at") or entry.get("updated_at"))
            items.append(
                build_item(
                    item_id=entry.get("id") or f"qiita-{idx}",
                    kind="article",
                    title=entry.get("title"),
                    url=entry.get("url"),
                    text=_body_for_mode(entry.get("body"), body_mode),
                    author=(entry.get("user") or {}).get("id"),
                    published_at=published_at,
                    source=self.channel,
                    extras={
                        "likes_count": entry.get("likes_count"),
                        "stocks_count": entry.get("stocks_count"),
                        "comments_count": entry.get("comments_count"),
                        "reactions_count": entry.get("reactions_count"),
                        "page_views_count": entry.get("page_views_count"),
                        "private": entry.get("private"),
                        "tags": [tag.get("name") for tag in entry.get("tags") or [] if tag.get("name")],
                        "updated_at": parse_timestamp(entry.get("updated_at")),
                        "source_hints": article_source_hints(published_at),
                    },
                )
            )
        raw_output = [_entry_for_body_mode(entry, body_mode) for entry in raw]
        total_count = response.headers.get("Total-Count")

        return self.ok_result(
            "search",
            items=items,
            raw=raw_output,
            meta=self.make_meta(
                value=query,
                limit=limit,
                started_at=started_at,
                total_count=total_count,
                body_mode=body_mode,
                **build_pagination_meta(
                    limit=limit,
                    page_size=len(raw),
                    pages_fetched=1,
                    has_more=_has_more(total_count, len(raw_output)),
                    total_available=total_count,
                ),
            ),
        )


def _body_for_mode(body: object, body_mode: str) -> str | None:
    if body is None:
        return None
    text = str(body)
    if body_mode == "none":
        return None
    if body_mode == "snippet":
        return text[:_BODY_SNIPPET_CHARS]
    return text


def _entry_for_body_mode(entry: dict, body_mode: str) -> dict:
    if body_mode == "full":
        return entry
    output = dict(entry)
    if body_mode == "none":
        output.pop("body", None)
    elif body_mode == "snippet" and "body" in output:
        output["body"] = _body_for_mode(output.get("body"), body_mode)
    return output


def _has_more(total_count: str | int | None, returned_count: int) -> bool | None:
    if total_count is None:
        return None
    try:
        return int(total_count) > returned_count
    except (TypeError, ValueError):
        return None
