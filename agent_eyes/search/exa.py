# -*- coding: utf-8 -*-
"""Exa semantic web search.

Get a free API key at https://exa.ai (1000 searches/month free).
"""

import os
import requests
from loguru import logger
from typing import Any, Dict, List, Optional


EXA_API_URL = "https://api.exa.ai/search"


def _get_api_key(config=None) -> str:
    """Get Exa API key from config or env."""
    if config:
        key = config.get("exa_api_key")
        if key:
            return key
    key = os.environ.get("EXA_API_KEY")
    if key:
        return key
    raise ValueError(
        "Exa API key not configured.\n"
        "Get a free key at https://exa.ai (1000 searches/month free)\n"
        "Then run: agent-eyes setup"
    )


async def search_web(
    query: str,
    num_results: int = 5,
    search_type: str = "auto",
    config=None,
) -> List[Dict[str, Any]]:
    """
    Semantic web search via Exa.

    Args:
        query: Search query (supports site: prefix)
        num_results: Number of results (default 5, max 10)
        search_type: "auto" / "neural" / "keyword"
        config: Optional Config instance

    Returns:
        List of {title, url, snippet, published_date, score}
    """
    api_key = _get_api_key(config)
    logger.info(f"Exa search: {query} (n={num_results})")

    resp = requests.post(
        EXA_API_URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
        },
        json={
            "query": query,
            "numResults": min(num_results, 10),
            "type": search_type,
            "contents": {"text": {"maxCharacters": 500}},
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("text", ""),
            "published_date": item.get("publishedDate", ""),
            "score": item.get("score", 0),
        })
    return results
