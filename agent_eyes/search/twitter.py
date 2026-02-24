# -*- coding: utf-8 -*-
"""Twitter search — uses birdx if available, falls back to Exa."""

import json
import shutil
import subprocess
from loguru import logger
from typing import Any, Dict, List, Optional


async def search_twitter(
    query: str,
    limit: int = 10,
    config=None,
) -> List[Dict[str, Any]]:
    """
    Search Twitter/X content.

    Strategy:
    1. If birdx is installed → use it (full search, timeline, threads)
    2. Otherwise → use Exa with site:x.com (basic search)

    Args:
        query: Search query
        limit: Number of results
        config: Optional Config instance

    Returns:
        List of {author, text, url, likes, retweets, date}
    """
    if shutil.which("birdx"):
        return await _search_birdx(query, limit)
    else:
        return await _search_exa(query, limit, config)


async def _search_birdx(query: str, limit: int) -> List[Dict[str, Any]]:
    """Search Twitter via birdx CLI."""
    logger.info(f"birdx search: {query} (n={limit})")
    try:
        result = subprocess.run(
            ["birdx", "search", query, "-n", str(limit), "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            # birdx might not support --json, try plain output
            result = subprocess.run(
                ["birdx", "search", query, "-n", str(limit)],
                capture_output=True, text=True, timeout=30,
            )
            return _parse_birdx_text(result.stdout)

        data = json.loads(result.stdout)
        if isinstance(data, list):
            return data
        return data.get("tweets", data.get("results", []))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"birdx search failed: {e}")
        return []


def _parse_birdx_text(text: str) -> List[Dict[str, Any]]:
    """Parse birdx plain text output into structured data."""
    results = []
    current = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            if current:
                results.append(current)
                current = {}
            continue
        if line.startswith("@"):
            current["author"] = line.split()[0] if line else ""
        elif line.startswith("http"):
            current["url"] = line
        else:
            current["text"] = current.get("text", "") + " " + line
    if current:
        results.append(current)
    return results


async def _search_exa(query: str, limit: int, config=None) -> List[Dict[str, Any]]:
    """Search Twitter via Exa (site:x.com)."""
    from agent_eyes.search.exa import search_web
    return await search_web(
        f"site:x.com {query}",
        num_results=limit,
        config=config,
    )


async def get_user_tweets(
    username: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Get recent tweets from a user (requires birdx)."""
    if not shutil.which("birdx"):
        raise RuntimeError(
            "birdx not installed. Install: pip install birdx\n"
            "Then configure cookies: agent-eyes setup"
        )
    try:
        result = subprocess.run(
            ["birdx", "user-tweets", f"@{username.lstrip('@')}", "-n", str(limit)],
            capture_output=True, text=True, timeout=30,
        )
        return _parse_birdx_text(result.stdout)
    except subprocess.TimeoutExpired:
        logger.error("birdx timed out")
        return []
