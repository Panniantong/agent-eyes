# -*- coding: utf-8 -*-
"""External-facing collection adapters."""

from __future__ import annotations

from typing import Type

from agent_reach.config import Config

from .base import BaseAdapter
from .exa_search import ExaSearchAdapter
from .github import GitHubAdapter
from .rss import RSSAdapter
from .twitter import TwitterAdapter
from .web import WebAdapter
from .youtube import YouTubeAdapter

ADAPTERS: dict[str, Type[BaseAdapter]] = {
    "web": WebAdapter,
    "exa_search": ExaSearchAdapter,
    "github": GitHubAdapter,
    "youtube": YouTubeAdapter,
    "rss": RSSAdapter,
    "twitter": TwitterAdapter,
}


def get_adapter(name: str, config: Config | None = None) -> BaseAdapter | None:
    """Return a configured adapter for the requested channel."""

    adapter_cls = ADAPTERS.get(name)
    if adapter_cls is None:
        return None
    return adapter_cls(config=config)


__all__ = [
    "ADAPTERS",
    "BaseAdapter",
    "ExaSearchAdapter",
    "GitHubAdapter",
    "RSSAdapter",
    "TwitterAdapter",
    "WebAdapter",
    "YouTubeAdapter",
    "get_adapter",
]
