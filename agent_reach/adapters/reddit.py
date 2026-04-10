# -*- coding: utf-8 -*-
"""Reddit collection adapter backed by rdt-cli."""

from __future__ import annotations

import json
import re
import time
from typing import Any, cast
from urllib.parse import urlparse

from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    build_pagination_meta,
    derive_title_from_text,
    parse_timestamp,
)
from agent_reach.source_hints import forum_post_source_hints

from .base import BaseAdapter

_SUBREDDIT_QUERY_RE = re.compile(r"^(?:r/|subreddit:)(?P<subreddit>[A-Za-z0-9_]+)\s+(?P<query>.+)$")
_COMMENTS_ID_RE = re.compile(r"(?:/comments/|^t3_|^post[:/])(?P<id>[A-Za-z0-9_]+)", re.I)


def _permalink_url(permalink: object) -> str | None:
    if not permalink:
        return None
    text = str(permalink)
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return f"https://www.reddit.com{text}"


def _normalize_post_id(value: str) -> str:
    text = value.strip()
    match = _COMMENTS_ID_RE.search(text)
    if match:
        return match.group("id")
    parsed = urlparse(text)
    parts = [part for part in parsed.path.split("/") if part]
    if "comments" in parts:
        idx = parts.index("comments")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    if text.startswith("reddit:"):
        text = text[7:]
    return text.removeprefix("t3_")


def _search_query(value: str) -> tuple[str, str | None]:
    text = value.strip()
    match = _SUBREDDIT_QUERY_RE.match(text)
    if not match:
        return text, None
    return match.group("query").strip(), match.group("subreddit")


def _post_item(data: dict[str, Any], idx: int, *, source: str) -> NormalizedItem:
    item_id = str(data.get("name") or data.get("id") or f"reddit-post-{idx}")
    published_at = parse_timestamp(data.get("created_utc") or data.get("created"))
    permalink = _permalink_url(data.get("permalink"))
    return build_item(
        item_id=item_id,
        kind="reddit_post",
        title=data.get("title"),
        url=permalink,
        text=data.get("selftext") or data.get("selftext_html"),
        author=data.get("author"),
        published_at=published_at,
        source=source,
        extras={
            "subreddit": data.get("subreddit"),
            "subreddit_name_prefixed": data.get("subreddit_name_prefixed"),
            "score": data.get("score"),
            "ups": data.get("ups"),
            "num_comments": data.get("num_comments"),
            "domain": data.get("domain"),
            "external_url": data.get("url") if data.get("url") != permalink else None,
            "is_self": data.get("is_self"),
            "over_18": data.get("over_18"),
            "link_flair_text": data.get("link_flair_text"),
            "stickied": data.get("stickied"),
            "locked": data.get("locked"),
            "source_hints": forum_post_source_hints(published_at),
        },
    )


def _comment_item(
    data: dict[str, Any],
    idx: int,
    *,
    source: str,
    post_title: str | None = None,
) -> NormalizedItem:
    item_id = str(data.get("name") or data.get("id") or f"reddit-comment-{idx}")
    published_at = parse_timestamp(data.get("created_utc") or data.get("created"))
    text = data.get("body") or data.get("body_html")
    return build_item(
        item_id=item_id,
        kind="reddit_comment",
        title=derive_title_from_text(text, fallback=f"Comment by {data.get('author') or 'unknown'}"),
        url=_permalink_url(data.get("permalink")),
        text=text,
        author=data.get("author"),
        published_at=published_at,
        source=source,
        extras={
            "post_title": post_title,
            "parent_id": data.get("parent_id"),
            "link_id": data.get("link_id"),
            "subreddit": data.get("subreddit"),
            "score": data.get("score"),
            "ups": data.get("ups"),
            "depth": data.get("depth"),
            "stickied": data.get("stickied"),
            "source_hints": forum_post_source_hints(published_at),
        },
    )


def _listing_children(raw: object) -> list[dict[str, Any]]:
    data = raw.get("data") if isinstance(raw, dict) else {}
    raw_children = data.get("children") if isinstance(data, dict) else []
    children = raw_children if isinstance(raw_children, list) else []
    return [child for child in children if isinstance(child, dict)]


def _listing_metadata(raw: object) -> dict[str, Any]:
    data = raw.get("data") if isinstance(raw, dict) else None
    return data if isinstance(data, dict) else {}


def _flatten_comment_children(children: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []

    def visit(node: dict[str, Any]) -> None:
        if len(flattened) >= limit:
            return
        if node.get("kind") == "more":
            return
        data = node.get("data")
        if not isinstance(data, dict):
            return
        flattened.append(data)
        replies = data.get("replies")
        if isinstance(replies, dict):
            for child in _listing_children(replies):
                visit(child)

    for child in children:
        visit(child)
        if len(flattened) >= limit:
            break
    return flattened


def _decode_first_json(raw_output: str) -> object | None:
    text = raw_output.strip()
    if not text:
        return None
    decoder = json.JSONDecoder()
    try:
        payload, _end = decoder.raw_decode(text)
        return payload
    except json.JSONDecodeError:
        pass

    for idx, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            payload, _end = decoder.raw_decode(text[idx:])
            return payload
        except json.JSONDecodeError:
            continue
    return None


def _unwrap_rdt_payload(payload: object) -> tuple[object, object]:
    if isinstance(payload, dict) and "ok" in payload:
        return payload.get("data"), payload
    return payload, payload


def _comment_data_from_raw(raw: object, *, limit: int) -> list[dict[str, Any]]:
    if isinstance(raw, dict):
        comments = raw.get("comments")
        if isinstance(comments, list):
            normalized = []
            for comment in comments[:limit]:
                if isinstance(comment, dict):
                    data = comment.get("data")
                    normalized.append(data if isinstance(data, dict) else comment)
            return normalized

    if isinstance(raw, list):
        return _flatten_comment_children(
            _listing_children(raw[1]) if len(raw) > 1 else [],
            limit=limit,
        )

    return []


def _post_data_from_raw(raw: object) -> dict[str, Any] | None:
    if isinstance(raw, dict):
        post = raw.get("post") or raw.get("submission")
        if isinstance(post, dict):
            data = post.get("data")
            return data if isinstance(data, dict) else post
        children = _listing_children(raw)
        if children and isinstance(children[0].get("data"), dict):
            return children[0]["data"]

    if isinstance(raw, list) and raw:
        children = _listing_children(raw[0])
        if children and isinstance(children[0].get("data"), dict):
            return children[0]["data"]

    return None


class RedditAdapter(BaseAdapter):
    """Read Reddit search results and public threads through rdt-cli."""

    channel = "reddit"
    operations = ("search", "read")

    def search(self, query: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        search_query, subreddit = _search_query(query)
        if not search_query:
            return self.error_result(
                "search",
                code="invalid_input",
                message="Reddit search input must include a query",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        command = ["search", search_query, "-n", str(limit), "--json"]
        if subreddit:
            command.extend(["-r", subreddit])
        raw = self._run_rdt(
            command,
            operation="search",
            value=query,
            limit=limit,
            started_at=started_at,
        )
        if _is_error_result(raw):
            return cast(CollectionResult, raw)
        listing, raw_payload = _unwrap_rdt_payload(raw)
        if not isinstance(listing, dict):
            return self.error_result(
                "search",
                code="invalid_response",
                message="rdt search returned an unexpected payload",
                raw=raw_payload,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        children = _listing_children(listing)
        items = [
            _post_item(child.get("data") or {}, idx, source=self.channel)
            for idx, child in enumerate(children[:limit])
            if isinstance(child.get("data"), dict)
        ]
        metadata = _listing_metadata(listing)
        return self.ok_result(
            "search",
            items=items,
            raw=raw_payload,
            meta=self.make_meta(
                value=query,
                limit=limit,
                started_at=started_at,
                subreddit=subreddit,
                backend="rdt_cli",
                **build_pagination_meta(
                    limit=limit,
                    page_size=len(children),
                    pages_fetched=1,
                    next_cursor=metadata.get("after"),
                    has_more=bool(metadata.get("after")),
                ),
            ),
        )

    def read(self, post_id_or_url: str, limit: int = 20) -> CollectionResult:
        started_at = time.perf_counter()
        post_id = _normalize_post_id(post_id_or_url)
        if not post_id:
            return self.error_result(
                "read",
                code="invalid_input",
                message="Reddit read input must be a post id or comments URL",
                meta=self.make_meta(value=post_id_or_url, limit=limit, started_at=started_at),
            )

        raw = self._run_rdt(
            ["read", post_id, "-n", str(limit), "--json"],
            operation="read",
            value=post_id,
            limit=limit,
            started_at=started_at,
        )
        if _is_error_result(raw):
            return cast(CollectionResult, raw)
        thread, raw_payload = _unwrap_rdt_payload(raw)

        post_data = _post_data_from_raw(thread)
        if post_data is None:
            return self.error_result(
                "read",
                code="not_found",
                message=f"Reddit post not found: {post_id}",
                raw=raw_payload,
                meta=self.make_meta(value=post_id, limit=limit, started_at=started_at),
            )

        post_item = _post_item(post_data, 0, source=self.channel)
        comments = _comment_data_from_raw(thread, limit=max(limit - 1, 0))
        comment_items = [
            _comment_item(comment, idx, source=self.channel, post_title=post_item["title"])
            for idx, comment in enumerate(comments, start=1)
        ]
        items = [post_item, *comment_items][:limit]
        raw_comment_children = _listing_children(thread[1]) if isinstance(thread, list) and len(thread) > 1 else comments
        return self.ok_result(
            "read",
            items=items,
            raw=raw_payload,
            meta=self.make_meta(
                value=post_id,
                limit=limit,
                started_at=started_at,
                backend="rdt_cli",
                comment_count=len(comment_items),
                **build_pagination_meta(
                    limit=limit,
                    page_size=len(items),
                    pages_fetched=1,
                    has_more=len(raw_comment_children) > len(comment_items),
                ),
            ),
        )

    def _run_rdt(
        self,
        args: list[str],
        *,
        operation: str,
        value: str,
        limit: int | None,
        started_at: float,
    ) -> object | CollectionResult:
        rdt = self.command_path("rdt")
        if not rdt:
            return self.error_result(
                operation,
                code="missing_dependency",
                message="rdt-cli is missing. Install it with `uv tool install rdt-cli`.",
                meta=self.make_meta(value=value, limit=limit, started_at=started_at, backend="rdt_cli"),
            )

        result = self.run_command([rdt, *args], timeout=120)
        if result.returncode != 0:
            return self.error_result(
                operation,
                code="command_failed",
                message=f"rdt {operation} failed with exit code {result.returncode}",
                raw={"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
                meta=self.make_meta(value=value, limit=limit, started_at=started_at, backend="rdt_cli"),
            )

        payload = _decode_first_json(result.stdout or "")
        if payload is None:
            return self.error_result(
                operation,
                code="invalid_response",
                message=f"rdt {operation} did not return JSON. Use `rdt {operation} --json` to verify the backend.",
                raw={"stdout": result.stdout, "stderr": result.stderr},
                meta=self.make_meta(value=value, limit=limit, started_at=started_at, backend="rdt_cli"),
            )
        if isinstance(payload, dict) and payload.get("ok") is False:
            error = payload.get("error")
            message = error.get("message") if isinstance(error, dict) else None
            return self.error_result(
                operation,
                code="command_failed",
                message=str(message or f"rdt {operation} returned an error"),
                raw=payload,
                meta=self.make_meta(value=value, limit=limit, started_at=started_at, backend="rdt_cli"),
            )
        return payload


def _is_error_result(value: object) -> bool:
    return isinstance(value, dict) and value.get("ok") is False and "error" in value
