# -*- coding: utf-8 -*-
"""
AgentEyes — the unified entry point.

Usage:
    from agent_eyes import AgentEyes

    eyes = AgentEyes()
    content = await eyes.read("https://github.com/openai/gpt-4")
    results = await eyes.search("AI agent framework")
"""

import asyncio
from typing import Any, Dict, List, Optional

from agent_eyes.config import Config
from agent_eyes.reader import UniversalReader


class AgentEyes:
    """Give your AI Agent eyes to see the entire internet."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.reader = UniversalReader()

    # ── Reading ─────────────────────────────────────────

    async def read(self, url: str) -> Dict[str, Any]:
        """
        Read content from any URL. Auto-detects platform.

        Supported: Web, GitHub, Reddit, Twitter, YouTube,
        Bilibili, WeChat, XiaoHongShu, RSS, Telegram, etc.

        Returns:
            Dict with title, content, url, author, etc.
        """
        content = await self.reader.read(url)
        return content.to_dict()

    async def read_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Read multiple URLs concurrently."""
        contents = await self.reader.read_batch(urls)
        return [c.to_dict() for c in contents]

    def detect_platform(self, url: str) -> str:
        """Detect what platform a URL belongs to."""
        return self.reader._detect_platform(url)

    # ── Searching ───────────────────────────────────────

    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic web search via Exa. Requires Exa API key.

        Args:
            query: Search query
            num_results: Number of results (max 10)
        """
        from agent_eyes.search.exa import search_web
        return await search_web(query, num_results=num_results, config=self.config)

    async def search_reddit(
        self,
        query: str,
        subreddit: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search Reddit via Exa (bypasses IP blocks).

        Args:
            query: Search query
            subreddit: Optional subreddit filter
            limit: Number of results
        """
        from agent_eyes.search.reddit import search_reddit
        return await search_reddit(query, subreddit=subreddit, num_results=limit, config=self.config)

    async def search_github(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub repositories.

        Args:
            query: Search query
            language: Filter by language
            limit: Number of results
        """
        from agent_eyes.search.github import search_github
        return await search_github(query, language=language, limit=limit, config=self.config)

    async def search_twitter(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search Twitter. Uses birdx if available, else Exa.

        Args:
            query: Search query
            limit: Number of results
        """
        from agent_eyes.search.twitter import search_twitter
        return await search_twitter(query, limit=limit, config=self.config)

    # ── Health ──────────────────────────────────────────

    def doctor(self) -> Dict[str, dict]:
        """Check all platform/feature availability."""
        from agent_eyes.doctor import check_all
        return check_all(self.config)

    def doctor_report(self) -> str:
        """Get formatted health report."""
        from agent_eyes.doctor import check_all, format_report
        return format_report(check_all(self.config))

    # ── Sync wrappers ───────────────────────────────────

    def read_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous version of read()."""
        return asyncio.run(self.read(url))

    def search_sync(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Synchronous version of search()."""
        return asyncio.run(self.search(query, num_results))
