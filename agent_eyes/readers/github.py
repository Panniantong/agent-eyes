# -*- coding: utf-8 -*-
"""GitHub fetcher — extracts repo info, issues, PRs, and README content.

Uses GitHub public API (no token needed for public repos).
For higher rate limits, set GITHUB_TOKEN env var.
"""

import os
import re
import base64
import requests
from loguru import logger
from typing import Dict, Any, List, Optional


API_BASE = "https://api.github.com"


def _get_headers() -> Dict[str, str]:
    """Get request headers, optionally with auth token."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AgentEyes/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _parse_github_url(url: str) -> Dict[str, str]:
    """Parse GitHub URL into components."""
    # Match: github.com/owner/repo[/type/number]
    match = re.search(
        r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/(issues|pull|tree|blob)/(.+))?/?$',
        url
    )
    if not match:
        raise ValueError(f"Cannot parse GitHub URL: {url}")

    return {
        "owner": match.group(1),
        "repo": match.group(2),
        "type": match.group(3),  # issues, pull, tree, blob, or None
        "ref": match.group(4),   # issue number, branch, file path, or None
    }


async def fetch_github(url: str) -> Dict[str, Any]:
    """Fetch content from a GitHub URL."""
    logger.info(f"Fetching GitHub: {url}")

    parsed = _parse_github_url(url)
    owner = parsed["owner"]
    repo = parsed["repo"]
    content_type = parsed["type"]
    ref = parsed["ref"]

    headers = _get_headers()

    if content_type == "issues" and ref:
        return await _fetch_issue(owner, repo, ref, headers)
    elif content_type == "pull" and ref:
        return await _fetch_pull(owner, repo, ref, headers)
    else:
        return await _fetch_repo(owner, repo, headers)


async def _fetch_repo(owner: str, repo: str, headers: Dict) -> Dict[str, Any]:
    """Fetch repo info + README."""
    # Get repo info
    repo_resp = requests.get(f"{API_BASE}/repos/{owner}/{repo}", headers=headers, timeout=10)
    repo_resp.raise_for_status()
    repo_data = repo_resp.json()

    # Get README
    readme_content = ""
    try:
        readme_resp = requests.get(
            f"{API_BASE}/repos/{owner}/{repo}/readme",
            headers=headers, timeout=10,
        )
        if readme_resp.status_code == 200:
            readme_data = readme_resp.json()
            readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8")
    except Exception as e:
        logger.warning(f"Could not fetch README: {e}")

    return {
        "title": f"{owner}/{repo}",
        "content": readme_content or repo_data.get("description", ""),
        "description": repo_data.get("description", ""),
        "author": owner,
        "url": repo_data.get("html_url", ""),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "language": repo_data.get("language", ""),
        "topics": repo_data.get("topics", []),
        "license": (repo_data.get("license") or {}).get("spdx_id", ""),
        "platform": "github",
    }


async def _fetch_issue(owner: str, repo: str, number: str, headers: Dict) -> Dict[str, Any]:
    """Fetch a GitHub issue with comments."""
    issue_num = re.match(r'(\d+)', number).group(1)

    # Get issue
    resp = requests.get(
        f"{API_BASE}/repos/{owner}/{repo}/issues/{issue_num}",
        headers=headers, timeout=10,
    )
    resp.raise_for_status()
    issue = resp.json()

    # Get comments
    comments_text = ""
    if issue.get("comments", 0) > 0:
        c_resp = requests.get(
            f"{API_BASE}/repos/{owner}/{repo}/issues/{issue_num}/comments",
            headers=headers, params={"per_page": 20}, timeout=10,
        )
        if c_resp.status_code == 200:
            comments = c_resp.json()
            parts = ["\n---\n## Comments\n"]
            for c in comments:
                parts.append(f"**@{c.get('user', {}).get('login', '?')}**:\n{c.get('body', '')}\n")
            comments_text = "\n".join(parts)

    return {
        "title": f"[{owner}/{repo}#{issue_num}] {issue.get('title', '')}",
        "content": (issue.get("body", "") or "") + comments_text,
        "author": issue.get("user", {}).get("login", ""),
        "url": issue.get("html_url", ""),
        "state": issue.get("state", ""),
        "labels": [l.get("name", "") for l in issue.get("labels", [])],
        "platform": "github",
    }


async def _fetch_pull(owner: str, repo: str, number: str, headers: Dict) -> Dict[str, Any]:
    """Fetch a GitHub pull request."""
    pr_num = re.match(r'(\d+)', number).group(1)

    resp = requests.get(
        f"{API_BASE}/repos/{owner}/{repo}/pulls/{pr_num}",
        headers=headers, timeout=10,
    )
    resp.raise_for_status()
    pr = resp.json()

    return {
        "title": f"[{owner}/{repo}#{pr_num}] {pr.get('title', '')}",
        "content": pr.get("body", "") or "",
        "author": pr.get("user", {}).get("login", ""),
        "url": pr.get("html_url", ""),
        "state": pr.get("state", ""),
        "merged": pr.get("merged", False),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "changed_files": pr.get("changed_files", 0),
        "platform": "github",
    }


async def search_github(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search GitHub repositories."""
    logger.info(f"Searching GitHub: {query}")

    resp = requests.get(
        f"{API_BASE}/search/repositories",
        headers=_get_headers(),
        params={"q": query, "sort": "stars", "per_page": limit},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("full_name", ""),
            "description": item.get("description", ""),
            "url": item.get("html_url", ""),
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language", ""),
            "updated_at": item.get("updated_at", ""),
        })

    return results
