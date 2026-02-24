# -*- coding: utf-8 -*-
"""
X/Twitter fetcher — three-tier fallback:

1. X oEmbed API (fast, reliable for individual tweets, no login needed)
2. Jina Reader (handles non-tweet X pages like profiles)
3. Playwright + saved session (handles login-required content)

Install browser tier: pip install "x-reader[browser]" && playwright install chromium
Save X session:       x-reader login twitter
"""

import re
import requests
from loguru import logger
from typing import Dict, Any

from agent_eyes.fetchers.jina import fetch_via_jina


OEMBED_URL = "https://publish.twitter.com/oembed"


def _extract_author(url: str) -> str:
    """Extract @username from tweet URL."""
    match = re.search(r'x\.com/(\w+)/status', url)
    return f"@{match.group(1)}" if match else ""


def _is_tweet_url(url: str) -> bool:
    """Check if this is a direct tweet/status URL (vs profile or other X page)."""
    return bool(re.search(r'x\.com/\w+/status/\d+', url))


def _fetch_via_oembed(url: str) -> Dict[str, Any]:
    """
    Fetch tweet text via X's oEmbed API.
    Free, reliable, no auth needed. Works for public tweets.
    Note: oEmbed requires twitter.com URLs (not x.com).
    """
    # oEmbed API requires twitter.com format
    oembed_query_url = url.replace("x.com", "twitter.com")
    resp = requests.get(
        OEMBED_URL,
        params={"url": oembed_query_url, "omit_script": "true"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    # Strip HTML tags from the embedded HTML to get clean text
    html = data.get("html", "")
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()

    return {
        "text": text,
        "author": data.get("author_name", ""),
        "author_url": data.get("author_url", ""),
        "title": text[:100] if text else "",
    }


async def _fetch_via_playwright(url: str) -> Dict[str, Any]:
    """
    Fetch tweet via Playwright with X-specific DOM selectors.
    Uses saved login session if available (~/.x-reader/sessions/twitter.json).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright not installed. Run:\n"
            '  pip install "x-reader[browser]"\n'
            "  playwright install chromium"
        )

    from agent_eyes.fetchers.browser import get_session_path
    from pathlib import Path

    session_path = get_session_path("twitter")
    has_session = Path(session_path).exists()
    if has_session:
        logger.info(f"Using saved X session: {session_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context_kwargs = {}
        if has_session:
            context_kwargs["storage_state"] = session_path

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            **context_kwargs,
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Wait for tweet text to render (X is a SPA, needs JS execution)
            try:
                await page.wait_for_selector(
                    '[data-testid="tweetText"]', timeout=10_000
                )
            except Exception:
                pass  # May not appear if login required

            # Extract tweet content with X-specific selectors
            tweet_text = await page.evaluate("""() => {
                // Priority 1: tweet text element
                const tweetEl = document.querySelector('[data-testid="tweetText"]');
                if (tweetEl) return tweetEl.innerText;

                // Priority 2: article element (thread view)
                const article = document.querySelector('article');
                if (article) return article.innerText;

                // Priority 3: main content area
                const main = document.querySelector('main');
                if (main) return main.innerText;

                return '';
            }""")

            title = await page.title()

            return {
                "text": (tweet_text or "").strip(),
                "title": (title or "").strip()[:200],
            }
        finally:
            await context.close()
            await browser.close()


async def fetch_twitter(url: str) -> Dict[str, Any]:
    """
    Fetch a tweet or X post with three-tier fallback.

    Args:
        url: Tweet URL (x.com or twitter.com)

    Returns:
        Dict with: text, author, url, title, platform
    """
    url = url.replace("twitter.com", "x.com")
    author = _extract_author(url)

    # Tier 1: oEmbed API (best for individual tweets)
    if _is_tweet_url(url):
        try:
            logger.info(f"[Twitter] Tier 1 — oEmbed: {url}")
            data = _fetch_via_oembed(url)
            if data.get("text") and len(data["text"].strip()) > 20:
                return {
                    "text": data["text"],
                    "author": author or data.get("author", ""),
                    "url": url,
                    "title": data.get("title", ""),
                    "platform": "twitter",
                }
            logger.warning("[Twitter] oEmbed returned thin content")
        except Exception as e:
            logger.warning(f"[Twitter] oEmbed failed ({e})")

    # Tier 2: Jina Reader (handles profiles, threads, non-tweet pages)
    try:
        logger.info(f"[Twitter] Tier 2 — Jina: {url}")
        data = fetch_via_jina(url)
        content = data.get("content", "")
        title = data.get("title", "")
        jina_ok = (
            content
            and len(content.strip()) > 100
            and "not yet fully loaded" not in content.lower()
            and title.lower() not in ("x", "title: x", "")
        )
        if jina_ok:
            return {
                "text": content,
                "author": author,
                "url": url,
                "title": title,
                "platform": "twitter",
            }
        logger.warning("[Twitter] Jina returned unusable content")
    except Exception as e:
        logger.warning(f"[Twitter] Jina failed ({e})")

    # Tier 3: Playwright + session with X-specific extraction
    try:
        logger.info(f"[Twitter] Tier 3 — Playwright: {url}")
        data = await _fetch_via_playwright(url)
        content = data.get("text", "")
        if content and len(content.strip()) > 20:
            return {
                "text": content,
                "author": author,
                "url": url,
                "title": data.get("title", ""),
                "platform": "twitter",
            }
        logger.warning("[Twitter] Playwright returned empty content")
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"[Twitter] All methods failed: {e}")

    raise RuntimeError(
        f"❌ All Twitter fetch methods failed for: {url}\n"
        f"   Try: x-reader login twitter (to save session for browser fallback)\n"
        f"   Then retry: x-reader {url}"
    )
