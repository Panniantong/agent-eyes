# -*- coding: utf-8 -*-
"""
Xiaohongshu (RED) note fetcher — three-tier fallback:

1. Jina Reader (fast, no deps)
2. Playwright + saved session (handles 451/403)
3. Error with login instructions

Install browser tier: pip install "x-reader[browser]" && playwright install chromium
"""

from loguru import logger
from typing import Dict, Any
from pathlib import Path

from agent_eyes.fetchers.jina import fetch_via_jina


async def fetch_xhs(url: str) -> Dict[str, Any]:
    """
    Fetch a Xiaohongshu note with three-tier fallback.

    Args:
        url: xiaohongshu.com or xhslink.com URL

    Returns:
        Dict with: title, content, author, url, platform
    """
    # Tier 1: Jina Reader
    try:
        logger.info(f"[XHS] Tier 1 — Jina: {url}")
        data = fetch_via_jina(url)
        if data.get("content"):
            return {
                "title": data["title"],
                "content": data["content"],
                "author": data.get("author", ""),
                "url": url,
                "platform": "xhs",
            }
        logger.warning("[XHS] Jina returned empty content, falling back to browser")
    except Exception as e:
        logger.warning(f"[XHS] Jina failed ({e}), falling back to browser")

    # Tier 2: Playwright with session
    from agent_eyes.fetchers.browser import get_session_path, SESSION_DIR

    session_path = get_session_path("xhs")
    if not Path(session_path).exists():
        # Tier 3: No session — guide user
        raise RuntimeError(
            f"❌ XHS blocked Jina and no saved session found.\n"
            f"   Run: x-reader login xhs\n"
            f"   Then retry this URL."
        )

    try:
        logger.info(f"[XHS] Tier 2 — Playwright with session: {url}")
        from agent_eyes.fetchers.browser import fetch_via_browser

        data = await fetch_via_browser(url, storage_state=session_path)
        return {
            "title": data["title"],
            "content": data["content"],
            "author": data.get("author", ""),
            "url": url,
            "platform": "xhs",
        }
    except RuntimeError:
        # Playwright not installed
        raise
    except Exception as e:
        logger.error(f"[XHS] Browser fetch also failed: {e}")
        raise RuntimeError(
            f"❌ All XHS fetch methods failed.\n"
            f"   Last error: {e}\n"
            f"   Try: x-reader login xhs (to refresh session)"
        )
