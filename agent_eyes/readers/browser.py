# -*- coding: utf-8 -*-
"""
Playwright browser fetcher — headless Chromium fallback for anti-scraping sites.

Used when Jina Reader fails (403/451/timeout). Supports persistent login
sessions via Playwright's storage_state for platforms requiring authentication.

Install: pip install "x-reader[browser]" && playwright install chromium
"""

from loguru import logger
from pathlib import Path

SESSION_DIR = Path.home() / ".x-reader" / "sessions"
TIMEOUT_MS = 30_000


async def fetch_via_browser(url: str, storage_state: str = None) -> dict:
    """
    Fetch a URL using headless Chromium via Playwright.

    Args:
        url: Target URL to fetch.
        storage_state: Path to a Playwright storage state JSON file (cookies/localStorage).
                       If provided, the browser context will load this session.

    Returns:
        dict with keys: title, content, url, author
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed. Run:\n"
            '  pip install "x-reader[browser]"\n'
            "  playwright install chromium"
        )

    logger.info(f"Browser fetch: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context_kwargs = {}
        if storage_state and Path(storage_state).exists():
            context_kwargs["storage_state"] = storage_state
            logger.info(f"Using session: {storage_state}")

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            **context_kwargs,
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
            # Extra wait for JS-heavy pages
            await page.wait_for_timeout(2000)

            title = await page.title()
            # Extract main text content, stripping scripts/styles
            content = await page.evaluate("""() => {
                const el = document.querySelector('article')
                    || document.querySelector('main')
                    || document.querySelector('.content')
                    || document.body;
                return el ? el.innerText : '';
            }""")

            result = {
                "title": (title or "").strip()[:200],
                "content": (content or "").strip(),
                "url": url,
                "author": "",
            }
            logger.info(f"Browser fetch OK: {title[:60]}")
            return result

        finally:
            await context.close()
            await browser.close()


def get_session_path(platform: str) -> str:
    """Get the session file path for a platform."""
    return str(SESSION_DIR / f"{platform}.json")
