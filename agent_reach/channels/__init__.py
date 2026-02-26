# -*- coding: utf-8 -*-
"""
Channel registry — routes URLs to the right channel.

This is the core of Agent Reach' pluggable architecture.
Add a new channel: just create a file and register it here.
Swap a backend: just change the implementation inside the channel file.
"""

from typing import Dict, List, Optional
from .base import Channel, ReadResult, SearchResult

# Import all channels
from .web import WebChannel
from .github import GitHubChannel
from .twitter import TwitterChannel
from .youtube import YouTubeChannel
from .reddit import RedditChannel
from .rss import RSSChannel
from .bilibili import BilibiliChannel
from .exa_search import ExaSearchChannel
from .xiaohongshu import XiaoHongShuChannel
from .linkedin import LinkedInChannel
from .bosszhipin import BossZhipinChannel


# Channel registry — order matters (first match wins, web is last as fallback)
ALL_CHANNELS: List[Channel] = [
    GitHubChannel(),
    TwitterChannel(),
    YouTubeChannel(),
    RedditChannel(),
    BilibiliChannel(),
    XiaoHongShuChannel(),
    LinkedInChannel(),
    BossZhipinChannel(),
    RSSChannel(),
    ExaSearchChannel(),
    WebChannel(),        # Fallback — handles any URL
]

# Search-capable channels
SEARCH_CHANNELS: Dict[str, Channel] = {
    ch.name: ch for ch in ALL_CHANNELS if ch.can_search()
}


def get_channel_for_url(url: str) -> Channel:
    """Find the right channel for a URL."""
    for channel in ALL_CHANNELS:
        if channel.can_handle(url):
            return channel
    return WebChannel()  # Should never reach here, but just in case


def get_channel(name: str) -> Optional[Channel]:
    """Get a channel by name."""
    for ch in ALL_CHANNELS:
        if ch.name == name:
            return ch
    return None


def get_all_channels() -> List[Channel]:
    """Get all registered channels."""
    return ALL_CHANNELS


__all__ = [
    "Channel", "ReadResult", "SearchResult",
    "ALL_CHANNELS", "SEARCH_CHANNELS",
    "get_channel_for_url", "get_channel", "get_all_channels",
]
