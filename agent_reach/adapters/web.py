# -*- coding: utf-8 -*-
"""Web collection adapter."""

from __future__ import annotations

import re
import time
import warnings
from urllib.parse import urlparse

from agent_reach.results import (
    CollectionResult,
    build_item,
    derive_title_from_text,
    parse_timestamp,
)

from .base import BaseAdapter

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


def _normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def _extract_reader_metadata(markdown: str) -> tuple[str | None, str | None, str]:
    title_match = re.search(r"^Title:\s*(.+)$", markdown, re.MULTILINE)
    published_match = re.search(r"^Published Time:\s*(.+)$", markdown, re.MULTILINE)
    body_marker = "Markdown Content:"

    title = title_match.group(1).strip() if title_match else None
    published_at = parse_timestamp(published_match.group(1).strip()) if published_match else None
    if body_marker in markdown:
        body = markdown.split(body_marker, 1)[1].strip()
    else:
        body = markdown.strip()
    return title, published_at, body


def _title_from_markdown(url: str, markdown: str, fallback_title: str | None = None) -> str | None:
    if fallback_title:
        return fallback_title
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or derive_title_from_text(markdown, fallback=url)
    parsed = urlparse(url)
    return derive_title_from_text(markdown, fallback=parsed.netloc or url)


class WebAdapter(BaseAdapter):
    """Read generic web pages through Jina Reader."""

    channel = "web"
    operations = ("read",)

    def read(self, url: str, limit: int | None = None) -> CollectionResult:
        started_at = time.perf_counter()
        normalized = _normalize_url(url)
        requests = _import_requests()
        try:
            response = requests.get(
                f"https://r.jina.ai/{normalized}",
                headers={"User-Agent": _UA, "Accept": "text/plain"},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return self.error_result(
                "read",
                code="http_error",
                message=f"Web read failed: {exc}",
                meta=self.make_meta(value=normalized, limit=limit, started_at=started_at),
            )

        markdown = response.text
        title, published_at, body = _extract_reader_metadata(markdown)
        item = build_item(
            item_id=normalized,
            kind="page",
            title=_title_from_markdown(normalized, body, fallback_title=title),
            url=normalized,
            text=body,
            author=None,
            published_at=published_at,
            source=self.channel,
            extras={"reader_url": f"https://r.jina.ai/{normalized}"},
        )
        return self.ok_result(
            "read",
            items=[item],
            raw=markdown,
            meta=self.make_meta(value=normalized, limit=limit, started_at=started_at),
        )
