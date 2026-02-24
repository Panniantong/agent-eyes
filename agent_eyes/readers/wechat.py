# -*- coding: utf-8 -*-
"""
WeChat article fetcher — two-tier fallback:

1. Jina Reader (fast, no deps)
2. Playwright headless (no login needed for public articles)
"""

from loguru import logger
from typing import Dict, Any


async def fetch_wechat(url: str) -> Dict[str, Any]:
    """
    Fetch a WeChat public account article with fallback.

    Args:
        url: mp.weixin.qq.com article URL

    Returns:
        Dict with: title, content, author, url, platform
    """
    # Tier 1: Jina Reader
    try:
        logger.info(f"[WeChat] Tier 1 — Jina: {url}")
        from agent_eyes.fetchers.jina import fetch_via_jina

        data = fetch_via_jina(url)
        if data.get("content"):
            return {
                "title": data["title"],
                "content": data["content"],
                "author": data.get("author", ""),
                "url": url,
                "platform": "wechat",
            }
        logger.warning("[WeChat] Jina returned empty content, falling back to browser")
    except Exception as e:
        logger.warning(f"[WeChat] Jina failed ({e}), falling back to browser")

    # Tier 2: Playwright headless (no session needed)
    try:
        logger.info(f"[WeChat] Tier 2 — Playwright headless: {url}")
        from agent_eyes.fetchers.browser import fetch_via_browser

        data = await fetch_via_browser(url)
        return {
            "title": data["title"],
            "content": data["content"],
            "author": data.get("author", ""),
            "url": url,
            "platform": "wechat",
        }
    except RuntimeError:
        # Playwright not installed — re-raise with original Jina error context
        raise
    except Exception as e:
        logger.error(f"[WeChat] Browser fetch also failed: {e}")
        raise RuntimeError(
            f"❌ All WeChat fetch methods failed.\n"
            f"   Last error: {e}"
        )
