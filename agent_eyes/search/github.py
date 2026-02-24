# -*- coding: utf-8 -*-
"""GitHub search via public API (no key required)."""

import os
import requests
from loguru import logger
from typing import Any, Dict, List, Optional


GITHUB_API = "https://api.github.com"


def _get_headers(config=None) -> dict:
    """Get GitHub API headers with optional auth token."""
    headers = {"Accept": "application/vnd.github+json"}
    token = None
    if config:
        token = config.get("github_token")
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def search_github(
    query: str,
    language: Optional[str] = None,
    sort: str = "stars",
    limit: int = 5,
    config=None,
) -> List[Dict[str, Any]]:
    """
    Search GitHub repositories.

    Args:
        query: Search query
        language: Filter by language (e.g. "python")
        sort: Sort by "stars" / "forks" / "updated"
        limit: Number of results (max 30)
        config: Optional Config instance

    Returns:
        List of {name, url, description, stars, language, updated}
    """
    q = query
    if language:
        q += f" language:{language}"

    logger.info(f"GitHub search: {q} (n={limit})")

    resp = requests.get(
        f"{GITHUB_API}/search/repositories",
        headers=_get_headers(config),
        params={"q": q, "sort": sort, "per_page": min(limit, 30)},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for repo in data.get("items", []):
        results.append({
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "description": repo.get("description", ""),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language", ""),
            "updated": repo.get("updated_at", ""),
            "topics": repo.get("topics", []),
        })
    return results


async def search_github_issues(
    query: str,
    repo: Optional[str] = None,
    state: str = "open",
    limit: int = 5,
    config=None,
) -> List[Dict[str, Any]]:
    """
    Search GitHub issues and discussions.

    Args:
        query: Search query
        repo: Filter by repo (e.g. "owner/repo")
        state: "open" / "closed"
        limit: Number of results
        config: Optional Config instance
    """
    q = query
    if repo:
        q += f" repo:{repo}"
    q += f" state:{state}"

    resp = requests.get(
        f"{GITHUB_API}/search/issues",
        headers=_get_headers(config),
        params={"q": q, "sort": "reactions", "per_page": min(limit, 30)},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for issue in data.get("items", []):
        results.append({
            "title": issue.get("title", ""),
            "url": issue.get("html_url", ""),
            "body": (issue.get("body", "") or "")[:500],
            "state": issue.get("state", ""),
            "comments": issue.get("comments", 0),
            "reactions": issue.get("reactions", {}).get("total_count", 0),
            "created": issue.get("created_at", ""),
        })
    return results
