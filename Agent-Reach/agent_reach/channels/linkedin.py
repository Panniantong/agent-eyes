# -*- coding: utf-8 -*-
"""LinkedIn — via linkedin-scraper-mcp (MCP) or Jina Reader fallback.

Backend: linkedin-scraper-mcp (916 stars, Patchright browser automation)
Swap to: any LinkedIn access tool
"""

import shutil
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List


class LinkedInChannel(Channel):
    name = "linkedin"
    description = "LinkedIn 个人/公司 Profile 和职位"
    backends = ["linkedin-scraper-mcp", "Jina Reader"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "linkedin.com" in domain

    def check(self, config=None):
        if self._mcporter_has("linkedin"):
            return "ok", "完整可用（Profile、公司、职位搜索）"

        # Check if linkedin-scraper-mcp is installed as CLI
        if shutil.which("linkedin-scraper-mcp"):
            return "warn", (
                "linkedin-scraper-mcp 已安装但未接入 mcporter。运行：\n"
                "  1. linkedin-scraper-mcp --login（在有浏览器的机器上登录）\n"
                "  2. linkedin-scraper-mcp --transport streamable-http --port 8001\n"
                "  3. mcporter config add linkedin http://localhost:8001/mcp"
            )

        return "off", (
            "可通过 Jina Reader 读取部分内容。完整功能需要：\n"
            "  1. pip install linkedin-scraper-mcp\n"
            "  2. linkedin-scraper-mcp --login（在有浏览器的机器上登录）\n"
            "  3. linkedin-scraper-mcp --transport streamable-http --port 8001\n"
            "  4. mcporter config add linkedin http://localhost:8001/mcp\n"
            "  详见 https://github.com/stickerdaniel/linkedin-mcp-server"
        )

    async def read(self, url: str, config=None) -> ReadResult:
        path = urlparse(url).path.strip("/")

        # Try MCP first
        if self._mcporter_has("linkedin"):
            try:
                if "/in/" in url:
                    return await self._read_profile_mcp(url)
                elif "/company/" in url:
                    return await self._read_company_mcp(url)
                elif "/jobs/view/" in url:
                    return await self._read_job_mcp(url)
            except Exception:
                pass  # Fall through to Jina

        # Fallback: Jina Reader
        return await self._read_jina_linkedin(url)

    async def _read_profile_mcp(self, url: str) -> ReadResult:
        """Read a LinkedIn profile via MCP."""
        import re
        # Extract username from URL: /in/username/
        match = re.search(r"/in/([^/]+)", url)
        if not match:
            return await self._read_jina_linkedin(url)
        username = match.group(1)
        safe_username = username.replace('"', '\\"')
        out = self._mcporter_call(
            f'linkedin.get_person_profile(linkedin_username: "{safe_username}")',
            timeout=60,
        )
        return ReadResult(
            title=self._extract_first_line(out) or f"LinkedIn Profile - {username}",
            content=out.strip(),
            url=url,
            platform="linkedin",
        )

    async def _read_company_mcp(self, url: str) -> ReadResult:
        """Read a LinkedIn company page via MCP."""
        import re
        # Extract company name from URL: /company/name/
        match = re.search(r"/company/([^/]+)", url)
        if not match:
            return await self._read_jina_linkedin(url)
        company = match.group(1)
        safe_company = company.replace('"', '\\"')
        out = self._mcporter_call(
            f'linkedin.get_company_profile(company_name: "{safe_company}")',
            timeout=60,
        )
        return ReadResult(
            title=self._extract_first_line(out) or "LinkedIn Company",
            content=out.strip(),
            url=url,
            platform="linkedin",
        )

    async def _read_job_mcp(self, url: str) -> ReadResult:
        """Read a LinkedIn job posting via MCP."""
        import re
        match = re.search(r"/jobs/view/(\d+)", url)
        if not match:
            return await self._read_jina_linkedin(url)

        job_id = match.group(1)
        out = self._mcporter_call(
            f'linkedin.get_job_details(job_id: "{job_id}")',
            timeout=30,
        )
        return ReadResult(
            title=self._extract_first_line(out) or f"LinkedIn Job {job_id}",
            content=out.strip(),
            url=url,
            platform="linkedin",
        )

    async def _read_jina_linkedin(self, url: str) -> ReadResult:
        """Jina fallback with LinkedIn-specific usability check."""
        result = await self._jina_read(url, "linkedin")
        text = result.content

        # Check if content is usable
        if len(text.strip()) < 100 or "Sign in" in text[:200]:
            return ReadResult(
                title="LinkedIn",
                content=(
                    f"⚠️ LinkedIn 页面需要登录才能完整查看。\n\n"
                    f"URL: {url}\n\n"
                    "完整功能需安装 linkedin-scraper-mcp：\n"
                    "  pip install linkedin-scraper-mcp\n"
                    "  uvx linkedin-scraper-mcp --login\n"
                    "  详见 https://github.com/stickerdaniel/linkedin-mcp-server"
                ),
                url=url,
                platform="linkedin",
            )

        return result

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        limit = kwargs.get("limit", 10)

        # Try MCP search first
        if self._mcporter_has("linkedin"):
            try:
                return await self._search_mcp(query, limit)
            except Exception:
                pass

        # Fallback to Exa
        from agent_reach.channels.exa_search import ExaSearchChannel
        exa = ExaSearchChannel()
        return await exa.search(f"site:linkedin.com {query}", config=config, limit=limit)

    async def _search_mcp(self, query: str, limit: int) -> List[SearchResult]:
        """Search LinkedIn via MCP."""
        safe_q = query.replace('"', '\\"')
        # Try job search first (most common use case)
        try:
            out = self._mcporter_call(
                f'linkedin.search_jobs(keywords: "{safe_q}")',
                timeout=60,
            )
            results = self._parse_search_results(out, "job")
            if results:
                return results[:limit]
        except Exception:
            pass

        # Try people search
        try:
            out = self._mcporter_call(
                f'linkedin.search_people(keywords: "{safe_q}")',
                timeout=60,
            )
            results = self._parse_search_results(out, "people")
            if results:
                return results
        except Exception:
            pass

        return []

    def _parse_search_results(self, text: str, result_type: str) -> List[SearchResult]:
        """Parse MCP search output into SearchResults."""
        import json
        results = []
        try:
            data = json.loads(text)
            items = data if isinstance(data, list) else data.get("results", data.get("jobs", []))
            for item in items:
                if isinstance(item, dict):
                    title = item.get("title") or item.get("name") or item.get("headline", "")
                    url = item.get("url") or item.get("link", "")
                    snippet = item.get("description") or item.get("company", "")
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet[:200] if snippet else "",
                    ))
        except (json.JSONDecodeError, KeyError):
            # Try line-by-line parsing
            pass
        return results
