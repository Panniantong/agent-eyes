# -*- coding: utf-8 -*-
"""Reddit fetcher — extracts posts and comments via JSON API.

Supports optional proxy via REDDIT_PROXY env var (many IPs are blocked by Reddit).
Example: REDDIT_PROXY=http://user:pass@host:port
"""

import os
import re
import requests
from loguru import logger
from typing import Dict, Any, List, Optional


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}


def _get_proxies() -> Optional[Dict[str, str]]:
    """Get proxy config from env."""
    proxy = os.environ.get("REDDIT_PROXY")
    if proxy:
        return {"http": proxy, "https": proxy}
    return None


def _extract_post(post_data: Dict) -> Dict[str, Any]:
    """Extract post info from Reddit JSON."""
    data = post_data.get("data", {})
    return {
        "title": data.get("title", ""),
        "author": data.get("author", "[deleted]"),
        "selftext": data.get("selftext", ""),
        "score": data.get("score", 0),
        "num_comments": data.get("num_comments", 0),
        "url": f"https://www.reddit.com{data.get('permalink', '')}",
        "created_utc": data.get("created_utc", 0),
        "subreddit": data.get("subreddit", ""),
    }


def _extract_comments(comments_data: Dict, limit: int = 20) -> List[Dict[str, str]]:
    """Extract top-level comments."""
    comments = []
    children = comments_data.get("data", {}).get("children", [])
    for child in children[:limit]:
        if child.get("kind") != "t1":
            continue
        data = child.get("data", {})
        comments.append({
            "author": data.get("author", "[deleted]"),
            "body": data.get("body", ""),
            "score": data.get("score", 0),
        })
    return comments


async def fetch_reddit(url: str) -> Dict[str, Any]:
    """Fetch Reddit post + comments via JSON API."""
    logger.info(f"Fetching Reddit: {url}")

    # Normalize URL and append .json
    clean_url = re.sub(r'\?.*$', '', url.rstrip('/'))
    json_url = f"{clean_url}.json"

    resp = requests.get(
        json_url,
        headers=HEADERS,
        proxies=_get_proxies(),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    # Reddit returns [post_listing, comments_listing]
    if not isinstance(data, list) or len(data) < 2:
        raise ValueError(f"Unexpected Reddit response format")

    post_listing = data[0].get("data", {}).get("children", [])
    if not post_listing:
        raise ValueError("No post found")

    post = _extract_post(post_listing[0])
    comments = _extract_comments(data[1])

    # Build readable content
    content_parts = [post["selftext"]] if post["selftext"] else []
    if comments:
        content_parts.append("\n---\n## Top Comments\n")
        for c in comments:
            content_parts.append(f"**u/{c['author']}** ({c['score']} pts):\n{c['body']}\n")

    return {
        "title": post["title"],
        "content": "\n".join(content_parts),
        "author": f"u/{post['author']}",
        "url": post["url"],
        "subreddit": post["subreddit"],
        "score": post["score"],
        "num_comments": post["num_comments"],
        "platform": "reddit",
    }


async def search_reddit(query: str, subreddit: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search Reddit posts."""
    logger.info(f"Searching Reddit: {query} (sub={subreddit})")

    if subreddit:
        search_url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "restrict_sr": "on", "limit": limit, "sort": "relevance"}
    else:
        search_url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": limit, "sort": "relevance"}

    resp = requests.get(
        search_url,
        headers=HEADERS,
        params=params,
        proxies=_get_proxies(),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for child in data.get("data", {}).get("children", []):
        results.append(_extract_post(child))

    return results
