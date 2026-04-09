# -*- coding: utf-8 -*-
"""GitHub collection adapter."""

from __future__ import annotations

import json
import time
from urllib.parse import urlparse

from agent_reach.results import CollectionResult, NormalizedItem, build_item, parse_timestamp

from .base import BaseAdapter


def _normalize_repository(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    if "github.com" not in text:
        return text if "/" in text else None
    parsed = urlparse(text)
    segments = [segment for segment in parsed.path.split("/") if segment]
    if len(segments) < 2:
        return None
    return f"{segments[0]}/{segments[1]}"


class GitHubAdapter(BaseAdapter):
    """Read and search GitHub repositories through gh CLI."""

    channel = "github"
    operations = ("search", "read")

    def search(self, query: str, limit: int = 5) -> CollectionResult:
        started_at = time.perf_counter()
        gh = self.command_path("gh")
        if not gh:
            return self.error_result(
                "search",
                code="missing_dependency",
                message="gh CLI is missing. Install it with winget install --id GitHub.cli -e",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        try:
            result = self.run_command(
                [
                    gh,
                    "search",
                    "repos",
                    query,
                    "--limit",
                    str(limit),
                    "--json",
                    "name,fullName,description,url,updatedAt,stargazersCount,owner,language",
                ],
                timeout=60,
            )
        except Exception as exc:
            return self.error_result(
                "search",
                code="command_failed",
                message=f"GitHub search failed: {exc}",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        raw_output = f"{result.stdout}\n{result.stderr}".strip()
        if result.returncode != 0:
            return self.error_result(
                "search",
                code="command_failed",
                message="GitHub search command did not complete cleanly",
                raw=raw_output,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
                details={"returncode": result.returncode},
            )

        try:
            raw = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            return self.error_result(
                "search",
                code="invalid_response",
                message="GitHub search returned a non-JSON payload",
                raw=raw_output,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )
        items: list[NormalizedItem] = [
            build_item(
                item_id=repo.get("fullName") or repo.get("url") or repo.get("name") or f"github-{idx}",
                kind="repository",
                title=repo.get("fullName") or repo.get("name"),
                url=repo.get("url"),
                text=repo.get("description"),
                author=(repo.get("owner") or {}).get("login"),
                published_at=parse_timestamp(repo.get("updatedAt")),
                source=self.channel,
                extras={
                    "stars": repo.get("stargazersCount"),
                    "language": repo.get("language"),
                },
            )
            for idx, repo in enumerate(raw)
        ]
        return self.ok_result(
            "search",
            items=items,
            raw=raw,
            meta=self.make_meta(value=query, limit=limit, started_at=started_at),
        )

    def read(self, repository: str, limit: int | None = None) -> CollectionResult:
        started_at = time.perf_counter()
        gh = self.command_path("gh")
        if not gh:
            return self.error_result(
                "read",
                code="missing_dependency",
                message="gh CLI is missing. Install it with winget install --id GitHub.cli -e",
                meta=self.make_meta(value=repository, limit=limit, started_at=started_at),
            )

        repo_name = _normalize_repository(repository)
        if not repo_name:
            return self.error_result(
                "read",
                code="invalid_input",
                message="GitHub read expects owner/repo or a github.com repository URL",
                meta=self.make_meta(value=repository, limit=limit, started_at=started_at),
            )

        try:
            result = self.run_command(
                [
                    gh,
                    "repo",
                    "view",
                    repo_name,
                    "--json",
                    "name,nameWithOwner,description,url,owner,homepageUrl,stargazerCount,forkCount,updatedAt,createdAt,licenseInfo,primaryLanguage,isPrivate,isArchived,defaultBranchRef,repositoryTopics",
                ],
                timeout=60,
            )
        except Exception as exc:
            return self.error_result(
                "read",
                code="command_failed",
                message=f"GitHub read failed: {exc}",
                meta=self.make_meta(value=repo_name, limit=limit, started_at=started_at),
            )

        raw_output = f"{result.stdout}\n{result.stderr}".strip()
        if result.returncode != 0:
            return self.error_result(
                "read",
                code="command_failed",
                message="GitHub repo view did not complete cleanly",
                raw=raw_output,
                meta=self.make_meta(value=repo_name, limit=limit, started_at=started_at),
                details={"returncode": result.returncode},
            )

        try:
            raw = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return self.error_result(
                "read",
                code="invalid_response",
                message="GitHub repo view returned a non-JSON payload",
                raw=raw_output,
                meta=self.make_meta(value=repo_name, limit=limit, started_at=started_at),
            )
        item = build_item(
            item_id=raw.get("nameWithOwner") or repo_name,
            kind="repository",
            title=raw.get("nameWithOwner") or raw.get("name") or repo_name,
            url=raw.get("url"),
            text=raw.get("description"),
            author=(raw.get("owner") or {}).get("login"),
            published_at=parse_timestamp(raw.get("updatedAt")),
            source=self.channel,
            extras={
                "homepage_url": raw.get("homepageUrl"),
                "stars": raw.get("stargazerCount"),
                "forks": raw.get("forkCount"),
                "created_at": parse_timestamp(raw.get("createdAt")),
                "license": (raw.get("licenseInfo") or {}).get("name"),
                "primary_language": (raw.get("primaryLanguage") or {}).get("name"),
                "is_private": raw.get("isPrivate"),
                "is_archived": raw.get("isArchived"),
                "default_branch": (raw.get("defaultBranchRef") or {}).get("name"),
                "topics": [topic.get("name") for topic in raw.get("repositoryTopics") or [] if topic.get("name")],
            },
        )
        return self.ok_result(
            "read",
            items=[item],
            raw=raw,
            meta=self.make_meta(value=repo_name, limit=limit, started_at=started_at),
        )
