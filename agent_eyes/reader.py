# -*- coding: utf-8 -*-
"""
Universal Reader — routes any URL to the right fetcher.

The core dispatcher: give it a URL, get back structured content.
"""

import asyncio
from urllib.parse import urlparse
from loguru import logger
from typing import Dict, Any, Optional

from agent_eyes.schema import (
    UnifiedContent, UnifiedInbox, SourceType, MediaType,
    from_bilibili, from_twitter, from_wechat,
    from_xiaohongshu, from_youtube, from_rss, from_telegram,
)
from agent_eyes.readers.jina import fetch_via_jina


class UniversalReader:
    """
    Routes URLs to platform-specific fetchers.
    Falls back to Jina Reader for unknown platforms.
    """

    def __init__(self, inbox: Optional[UnifiedInbox] = None):
        self.inbox = inbox

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        domain = urlparse(url).netloc.lower()

        if "mp.weixin.qq.com" in domain:
            return "wechat"
        if "x.com" in domain or "twitter.com" in domain:
            return "twitter"
        if "youtube.com" in domain or "youtu.be" in domain:
            return "youtube"
        if "xiaohongshu.com" in domain or "xhslink.com" in domain:
            return "xhs"
        if "bilibili.com" in domain or "b23.tv" in domain:
            return "bilibili"
        if "xiaoyuzhoufm.com" in domain:
            return "podcast"
        if "podcasts.apple.com" in domain:
            return "podcast"
        if "t.me" in domain or "telegram.org" in domain:
            return "telegram"
        if "reddit.com" in domain or "redd.it" in domain:
            return "reddit"
        if "github.com" in domain:
            return "github"
        if url.endswith(".xml") or "/rss" in url or "/feed" in url or "/atom" in url:
            return "rss"
        return "generic"

    async def read(self, url: str) -> UnifiedContent:
        """
        Fetch content from any URL and return as UnifiedContent.

        The main entry point — give it a URL, get back structured content.
        """
        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        platform = self._detect_platform(url)
        logger.info(f"[{platform}] {url[:60]}...")

        try:
            content = await self._fetch(platform, url)

            # Save to inbox if configured
            if self.inbox:
                if self.inbox.add(content):
                    self.inbox.save()
                    logger.info(f"Saved to inbox: {content.title[:50]}")

            # Save to markdown output if configured
            from agent_eyes.utils.storage import save_to_markdown
            save_to_markdown(content)

            return content

        except Exception as e:
            logger.error(f"[{platform}] Failed: {e}")
            raise

    async def _fetch(self, platform: str, url: str) -> UnifiedContent:
        """Dispatch to platform-specific fetcher."""

        if platform == "bilibili":
            from agent_eyes.readers.bilibili import fetch_bilibili
            data = await fetch_bilibili(url)
            return from_bilibili(data)

        if platform == "twitter":
            from agent_eyes.readers.twitter import fetch_twitter
            data = await fetch_twitter(url)
            return from_twitter(data)

        if platform == "wechat":
            from agent_eyes.readers.wechat import fetch_wechat
            data = await fetch_wechat(url)
            return from_wechat(data)

        if platform == "xhs":
            from agent_eyes.readers.xhs import fetch_xhs
            data = await fetch_xhs(url)
            return from_xiaohongshu(data)

        if platform == "youtube":
            from agent_eyes.readers.youtube import fetch_youtube
            data = await fetch_youtube(url)
            return from_youtube(data)

        if platform == "rss":
            from agent_eyes.readers.rss import fetch_rss
            articles = await fetch_rss(url, limit=1)
            if articles:
                return from_rss(articles[0])
            raise ValueError(f"No articles found in RSS feed: {url}")

        if platform == "reddit":
            from agent_eyes.readers.reddit import fetch_reddit
            data = await fetch_reddit(url)
            return UnifiedContent(
                source_type=SourceType.REDDIT,
                source_name=f"r/{data.get('subreddit', '')}",
                title=data["title"],
                content=data.get("content", ""),
                url=data["url"],
                author=data.get("author", ""),
                media_type=MediaType.TEXT,
                metadata={"score": data.get("score", 0), "num_comments": data.get("num_comments", 0)},
            )

        if platform == "github":
            from agent_eyes.readers.github import fetch_github
            data = await fetch_github(url)
            return UnifiedContent(
                source_type=SourceType.GITHUB,
                source_name=data.get("title", ""),
                title=data["title"],
                content=data.get("content", ""),
                url=data["url"],
                author=data.get("author", ""),
                media_type=MediaType.TEXT,
                metadata={k: v for k, v in data.items() if k not in ("title", "content", "url", "author", "platform")},
            )

        if platform == "telegram":
            from agent_eyes.readers.telegram import fetch_telegram
            # Extract channel username from t.me URL
            path = urlparse(url).path.strip("/").split("/")[0]
            channel = path if path else url
            messages = await fetch_telegram(channel, limit=1)
            if messages:
                return from_telegram(messages[0], channel, channel)
            raise ValueError(f"No messages from Telegram channel: {url}")

        # Fallback: Jina Reader for any unknown URL
        logger.info(f"Using Jina fallback for: {url}")
        data = fetch_via_jina(url)
        return UnifiedContent(
            source_type=SourceType.MANUAL,
            source_name=urlparse(url).netloc,
            title=data["title"],
            content=data["content"],
            url=url,
        )

    async def read_batch(self, urls: list[str]) -> list[UnifiedContent]:
        """Fetch multiple URLs concurrently."""
        tasks = [self.read(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        contents = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Batch failed for {url}: {result}")
            else:
                contents.append(result)

        return contents
