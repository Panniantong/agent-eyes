# -*- coding: utf-8 -*-
"""Reddit search via Exa (bypasses Reddit IP blocks)."""

from typing import Any, Dict, List, Optional
from agent_eyes.search.exa import search_web


async def search_reddit(
    query: str,
    subreddit: Optional[str] = None,
    num_results: int = 10,
    config=None,
) -> List[Dict[str, Any]]:
    """
    Search Reddit content via Exa semantic search.

    Args:
        query: Search query
        subreddit: Optional subreddit (e.g. "LocalLLaMA")
        num_results: Number of results
        config: Optional Config instance

    Returns:
        List of {title, url, snippet, published_date, score}
    """
    if subreddit:
        full_query = f"site:reddit.com/r/{subreddit} {query}"
    else:
        full_query = f"site:reddit.com {query}"
    return await search_web(full_query, num_results=num_results, config=config)
