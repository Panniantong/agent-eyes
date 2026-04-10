# -*- coding: utf-8 -*-
"""Bluesky collection adapter."""

from __future__ import annotations

import time
import warnings
from typing import Any
from urllib.parse import urlencode

from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    derive_title_from_text,
    parse_timestamp,
)

from .base import BaseAdapter

_UA = "agent-reach"
_SEARCH_HOSTS = (
    "https://public.api.bsky.app",
    "https://api.bsky.app",
)


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


def _post_url(post: dict) -> str | None:
    author = post.get("author") or {}
    handle = author.get("handle")
    uri = post.get("uri") or ""
    rkey = uri.rstrip("/").split("/")[-1] if uri else None
    if handle and rkey:
        return f"https://bsky.app/profile/{handle}/post/{rkey}"
    return None


def _aspect_ratio(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    width = value.get("width")
    height = value.get("height")
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        return None
    if width <= 0 or height <= 0:
        return None
    return {
        "width": int(width),
        "height": int(height),
    }


def _media_from_embed(embed: Any) -> list[dict[str, Any]]:
    if not isinstance(embed, dict):
        return []

    media: list[dict[str, Any]] = []
    embed_type = str(embed.get("$type") or "")

    if embed_type.endswith("images#view"):
        for image in embed.get("images") or []:
            if not isinstance(image, dict):
                continue
            media.append(
                {
                    "type": "image",
                    "url": image.get("fullsize"),
                    "thumb_url": image.get("thumb"),
                    "alt": image.get("alt"),
                    "aspect_ratio": _aspect_ratio(image.get("aspectRatio")),
                }
            )

    if embed_type.endswith("video#view"):
        media.append(
            {
                "type": "video",
                "playlist_url": embed.get("playlist"),
                "thumb_url": embed.get("thumbnail"),
                "alt": embed.get("alt"),
                "aspect_ratio": _aspect_ratio(embed.get("aspectRatio")),
            }
        )

    nested_media = embed.get("media")
    if nested_media:
        media.extend(_media_from_embed(nested_media))
    return media


class BlueskyAdapter(BaseAdapter):
    """Search public Bluesky posts through the AppView API."""

    channel = "bluesky"
    operations = ("search",)

    def search(self, query: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        requests = _import_requests()
        params = {"q": query, "limit": str(limit)}
        headers = {"User-Agent": _UA, "Accept": "application/json"}
        attempts: list[dict[str, Any]] = []
        last_error: tuple[str, str, object | None, dict[str, Any] | None] | None = None

        for index, base_url in enumerate(_SEARCH_HOSTS):
            url = f"{base_url}/xrpc/app.bsky.feed.searchPosts?{urlencode(params)}"
            try:
                response = requests.get(url, headers=headers, timeout=30)
            except requests.RequestException as exc:
                attempts.append(
                    {
                        "api_base_url": base_url,
                        "error": "request_exception",
                        "message": str(exc),
                    }
                )
                last_error = (
                    "http_error",
                    f"Bluesky search failed at {base_url}: {exc}",
                    None,
                    {"attempts": list(attempts)},
                )
                continue

            raw_text = response.text
            if response.status_code >= 400:
                attempts.append(
                    {
                        "api_base_url": base_url,
                        "http_status": response.status_code,
                    }
                )
                last_error = (
                    "http_error",
                    f"Bluesky search returned HTTP {response.status_code} from {base_url}",
                    raw_text,
                    {"attempts": list(attempts)},
                )
                continue

            try:
                raw = response.json()
            except ValueError:
                attempts.append(
                    {
                        "api_base_url": base_url,
                        "error": "invalid_json",
                    }
                )
                last_error = (
                    "invalid_response",
                    f"Bluesky search returned a non-JSON payload from {base_url}",
                    raw_text,
                    {"attempts": list(attempts)},
                )
                continue

            posts = raw.get("posts")
            if not isinstance(posts, list):
                return self.error_result(
                    "search",
                    code="invalid_response",
                    message=f"Bluesky search payload from {base_url} did not include a posts list",
                    raw=raw,
                    meta=self.make_meta(
                        value=query,
                        limit=limit,
                        started_at=started_at,
                        api_base_url=base_url,
                        fallback_used=index > 0,
                    ),
                    details={"attempts": list(attempts)},
                )

            attempts.append(
                {
                    "api_base_url": base_url,
                    "http_status": response.status_code,
                }
            )
            items: list[NormalizedItem] = []
            for idx, post in enumerate(posts):
                author = post.get("author") or {}
                record = post.get("record") or {}
                embed = post.get("embed") or {}
                external = (embed.get("external") or {}) if isinstance(embed, dict) else {}
                title = derive_title_from_text(
                    record.get("text"),
                    fallback=external.get("title") or f"Bluesky post {idx + 1}",
                )
                items.append(
                    build_item(
                        item_id=post.get("uri") or post.get("cid") or f"bluesky-{idx}",
                        kind="post",
                        title=title,
                        url=_post_url(post),
                        text=record.get("text"),
                        author=author.get("handle"),
                        published_at=parse_timestamp(record.get("createdAt") or post.get("indexedAt")),
                        source=self.channel,
                        extras={
                            "author_display_name": author.get("displayName"),
                            "like_count": post.get("likeCount"),
                            "reply_count": post.get("replyCount"),
                            "repost_count": post.get("repostCount"),
                            "quote_count": post.get("quoteCount"),
                            "bookmark_count": post.get("bookmarkCount"),
                            "labels": post.get("labels") or [],
                            "media": _media_from_embed(embed),
                            "external_uri": external.get("uri"),
                            "external_title": external.get("title"),
                        },
                    )
                )

            return self.ok_result(
                "search",
                items=items,
                raw=raw,
                meta=self.make_meta(
                    value=query,
                    limit=limit,
                    started_at=started_at,
                    api_base_url=base_url,
                    fallback_used=index > 0,
                    attempted_hosts=[attempt["api_base_url"] for attempt in attempts],
                ),
            )

        if last_error is None:
            return self.error_result(
                "search",
                code="http_error",
                message="Bluesky search failed before any request could complete",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        code, message, raw, details = last_error
        return self.error_result(
            "search",
            code=code,
            message=message,
            raw=raw,
            meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            details=details,
        )
