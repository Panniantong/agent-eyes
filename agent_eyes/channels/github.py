# -*- coding: utf-8 -*-
"""GitHub — via GitHub REST API (free, no config needed).

Backend: GitHub API v3
Swap to: gh CLI, or any GitHub API wrapper
"""

import requests
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List


class GitHubChannel(Channel):
    name = "github"
    description = "GitHub 仓库和代码"
    backends = ["GitHub API"]
    tier = 0

    API = "https://api.github.com"

    def _headers(self, config=None):
        h = {"Accept": "application/vnd.github+json"}
        token = config.get("github_token") if config else None
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def check(self, config=None):
        import shutil
        token = config.get("github_token") if config else None
        has_gh = shutil.which("gh")
        if token or has_gh:
            return "ok", "完整可用（读取、搜索、Fork、Issue、PR 等）"
        return "ok", "公开仓库可读可搜。配置 gh CLI 或 github_token 可解锁 Fork、Issue、PR 等操作"

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "github.com" in domain

    async def read(self, url: str, config=None) -> ReadResult:
        path = urlparse(url).path.strip("/").split("/")

        if len(path) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")

        owner, repo = path[0], path[1]
        headers = self._headers(config)

        # Issues/PRs
        if len(path) >= 4 and path[2] in ("issues", "pull"):
            num = path[3]
            resp = requests.get(f"{self.API}/repos/{owner}/{repo}/issues/{num}", headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Get comments
            comments_text = ""
            if data.get("comments", 0) > 0:
                cr = requests.get(f"{self.API}/repos/{owner}/{repo}/issues/{num}/comments",
                                  headers=headers, params={"per_page": 20}, timeout=15)
                if cr.ok:
                    for c in cr.json():
                        comments_text += f"\n\n---\n**{c.get('user', {}).get('login', '')}** ({c.get('created_at', '')}):\n{c.get('body', '')}"

            return ReadResult(
                title=data.get("title", ""),
                content=(data.get("body", "") or "") + comments_text,
                url=url,
                author=data.get("user", {}).get("login", ""),
                date=data.get("created_at", ""),
                platform="github",
                extra={"state": data.get("state"), "comments": data.get("comments", 0),
                       "reactions": data.get("reactions", {}).get("total_count", 0)},
            )

        # Repo
        resp = requests.get(f"{self.API}/repos/{owner}/{repo}", headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Get README
        readme_text = ""
        rr = requests.get(f"{self.API}/repos/{owner}/{repo}/readme", headers=headers, timeout=15)
        if rr.ok:
            import base64
            readme_data = rr.json()
            if readme_data.get("encoding") == "base64":
                readme_text = base64.b64decode(readme_data["content"]).decode("utf-8", errors="replace")

        return ReadResult(
            title=f"{owner}/{repo}",
            content=readme_text or data.get("description", ""),
            url=url,
            author=owner,
            platform="github",
            extra={"stars": data.get("stargazers_count", 0), "forks": data.get("forks_count", 0),
                   "language": data.get("language", ""), "description": data.get("description", "")},
        )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        language = kwargs.get("language")
        limit = kwargs.get("limit", 5)

        q = query
        if language:
            q += f" language:{language}"

        resp = requests.get(
            f"{self.API}/search/repositories",
            headers=self._headers(config),
            params={"q": q, "sort": "stars", "per_page": min(limit, 30)},
            timeout=15,
        )
        resp.raise_for_status()

        results = []
        for repo in resp.json().get("items", []):
            results.append(SearchResult(
                title=repo.get("full_name", ""),
                url=repo.get("html_url", ""),
                snippet=repo.get("description", ""),
                date=repo.get("updated_at", ""),
                extra={"stars": repo.get("stargazers_count", 0),
                       "forks": repo.get("forks_count", 0),
                       "language": repo.get("language", "")},
            ))
        return results
