# -*- coding: utf-8 -*-
"""GitHub — via gh CLI.

Backend: gh CLI (https://cli.github.com)
Swap to: GitHub REST API
"""

import json
import shutil
import subprocess
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List


class GitHubChannel(Channel):
    name = "github"
    description = "GitHub 仓库和代码"
    backends = ["gh CLI"]
    tier = 0

    def _gh(self, args: list, timeout: int = 15) -> str:
        r = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr or r.stdout)
        return r.stdout

    def _gh_json(self, args: list, timeout: int = 15) -> dict:
        return json.loads(self._gh(args + ["--json"], timeout))

    def can_handle(self, url: str) -> bool:
        return "github.com" in urlparse(url).netloc.lower()

    def check(self, config=None):
        if not shutil.which("gh"):
            return "warn", "gh CLI 未安装。安装：https://cli.github.com 。公开仓库仍可通过 Jina Reader 读取"
        try:
            self._gh(["auth", "status"], timeout=5)
            return "ok", "完整可用（读取、搜索、Fork、Issue、PR 等）"
        except Exception:
            return "ok", "gh CLI 已装但未认证。运行 gh auth login 可解锁完整功能"

    async def read(self, url: str, config=None) -> ReadResult:
        if not shutil.which("gh"):
            # Fallback to Jina Reader for public repos
            from agent_reach.channels.web import WebChannel
            return await WebChannel().read(url, config)

        path = urlparse(url).path.strip("/").split("/")
        if len(path) < 2:
            from agent_reach.channels.web import WebChannel
            return await WebChannel().read(url, config)

        owner, repo = path[0], path[1]

        # Issues / PRs
        if len(path) >= 4 and path[2] in ("issues", "pull"):
            return await self._read_issue(owner, repo, path[3], url)

        # Repo
        return await self._read_repo(owner, repo, url)

    async def _read_repo(self, owner: str, repo: str, url: str) -> ReadResult:
        slug = f"{owner}/{repo}"
        try:
            # Get repo info
            info = self._gh(["repo", "view", slug])
            # Get README
            try:
                readme = self._gh(
                    ["api", f"repos/{slug}/readme", "--jq", ".content"],
                    timeout=10,
                )
                import base64
                readme_text = base64.b64decode(readme).decode("utf-8", errors="replace")
            except Exception:
                readme_text = ""

            content = readme_text or info
            return ReadResult(
                title=slug, content=content, url=url,
                author=owner, platform="github",
            )
        except Exception:
            from agent_reach.channels.web import WebChannel
            return await WebChannel().read(url)

    async def _read_issue(self, owner: str, repo: str, num: str, url: str) -> ReadResult:
        slug = f"{owner}/{repo}"
        try:
            out = self._gh(["issue", "view", num, "-R", slug])
            return ReadResult(
                title=f"{slug}#{num}", content=out, url=url,
                platform="github",
            )
        except Exception:
            # Might be a PR
            try:
                out = self._gh(["pr", "view", num, "-R", slug])
                return ReadResult(
                    title=f"{slug}#{num}", content=out, url=url,
                    platform="github",
                )
            except Exception:
                from agent_reach.channels.web import WebChannel
                return await WebChannel().read(url)

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        if not shutil.which("gh"):
            raise ValueError("GitHub search requires gh CLI. Install: https://cli.github.com")

        language = kwargs.get("language")
        limit = kwargs.get("limit", 5)

        args = ["search", "repos", query, "--sort", "stars", f"--limit={limit}"]
        if language:
            args += [f"--language={language}"]

        out = self._gh(args, timeout=15)
        results = []
        for line in out.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 1:
                slug = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""
                stars = parts[3].strip() if len(parts) > 3 else ""
                lang = parts[5].strip() if len(parts) > 5 else ""
                results.append(SearchResult(
                    title=slug,
                    url=f"https://github.com/{slug}",
                    snippet=desc,
                    extra={"stars": stars, "language": lang},
                ))
        return results
