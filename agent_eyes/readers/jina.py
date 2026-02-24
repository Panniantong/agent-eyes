# -*- coding: utf-8 -*-
"""
Jina Reader — universal fallback for content extraction.

Uses https://r.jina.ai/{url} to extract markdown from any web page.
Free, no API key required, handles JS rendering and anti-scraping.
"""

import requests
from loguru import logger


JINA_BASE = "https://r.jina.ai"
TIMEOUT = 30

HEADERS = {
    "Accept": "text/markdown",
    "User-Agent": "x-reader/0.1",
}


def fetch_via_jina(url: str) -> dict:
    """
    Fetch any URL via Jina Reader and return structured data.

    Returns:
        dict with keys: title, content, url, author (best-effort)
    """
    jina_url = f"{JINA_BASE}/{url}"
    logger.info(f"Jina fetch: {url}")

    try:
        resp = requests.get(jina_url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        text = resp.text

        # Jina returns markdown; first line is usually the title
        lines = text.strip().split("\n")
        title = ""
        content_lines = []

        for line in lines:
            if not title and line.strip():
                # First non-empty line as title, strip markdown heading
                title = line.lstrip("#").strip()
            else:
                content_lines.append(line)

        content = "\n".join(content_lines).strip()

        return {
            "title": title[:200],
            "content": content,
            "url": url,
            "author": "",
        }

    except requests.Timeout:
        logger.error(f"Jina timeout: {url}")
        raise
    except requests.RequestException as e:
        logger.error(f"Jina fetch failed: {url} — {e}")
        raise
