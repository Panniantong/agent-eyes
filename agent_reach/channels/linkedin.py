# -*- coding: utf-8 -*-
"""LinkedIn — via linkedin-scraper-mcp (MCP) or Jina Reader fallback.

Backend: linkedin-scraper-mcp (916 stars, Patchright browser automation)
Swap to: any LinkedIn access tool
"""

import json
import logging
import shutil
import subprocess
import time
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List
import requests

logger = logging.getLogger(__name__)

_mcporter_cache = {"available": None, "checked_at": 0}


def _mcporter_has_linkedin() -> bool:
    """Check if mcporter has linkedin MCP configured (cached for 60s)."""
    now = time.time()
    if now - _mcporter_cache["checked_at"] < 60 and _mcporter_cache["available"] is not None:
        return _mcporter_cache["available"]

    if not shutil.which("mcporter"):
        _mcporter_cache["available"] = False
        _mcporter_cache["checked_at"] = now
        return False
    try:
        r = subprocess.run(
            ["mcporter", "list"], capture_output=True, text=True, timeout=10
        )
        result = "linkedin" in r.stdout.lower()
    except Exception:
        result = False

    _mcporter_cache["available"] = result
    _mcporter_cache["checked_at"] = now
    return result


def _mcporter_call(expr: str, timeout: int = 30) -> str:
    """Call a LinkedIn MCP tool via mcporter."""
    r = subprocess.run(
        ["mcporter", "call", expr],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout)
    return r.stdout


class LinkedInChannel(Channel):
    name = "linkedin"
    description = "LinkedIn 个人/公司 Profile 和职位"
    backends = ["linkedin-scraper-mcp", "Jina Reader"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "linkedin.com" in domain

    def check(self, config=None):
        if _mcporter_has_linkedin():
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
        if _mcporter_has_linkedin():
            try:
                if "/in/" in url:
                    return await self._read_profile_mcp(url)
                elif "/company/" in url:
                    return await self._read_company_mcp(url)
                elif "/jobs/view/" in url:
                    return await self._read_job_mcp(url)
            except Exception as e:
                logger.warning(f"LinkedIn MCP read failed, falling back to Jina: {e}")

        # Fallback: Jina Reader
        return await self._read_jina(url)

    async def _read_profile_mcp(self, url: str) -> ReadResult:
        """Read a LinkedIn profile via MCP."""
        import re
        # Extract username from URL: /in/username/
        match = re.search(r"/in/([^/]+)", url)
        if not match:
            return await self._read_jina(url)
        username = match.group(1)
        safe_username = username.replace('"', '\\"')
        out = _mcporter_call(
            f'linkedin.get_person_profile(linkedin_username: "{safe_username}")',
            timeout=60,
        )
        return ReadResult(
            title=self._extract_title(out) or f"LinkedIn Profile - {username}",
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
            return await self._read_jina(url)
        company = match.group(1)
        safe_company = company.replace('"', '\\"')
        out = _mcporter_call(
            f'linkedin.get_company_profile(company_name: "{safe_company}")',
            timeout=60,
        )
        return ReadResult(
            title=self._extract_title(out) or "LinkedIn Company",
            content=out.strip(),
            url=url,
            platform="linkedin",
        )

    async def _read_job_mcp(self, url: str) -> ReadResult:
        """Read a LinkedIn job posting via MCP."""
        import re
        match = re.search(r"/jobs/view/(\d+)", url)
        if not match:
            return await self._read_jina(url)

        job_id = match.group(1)
        out = _mcporter_call(
            f'linkedin.get_job_details(job_id: "{job_id}")',
            timeout=30,
        )
        return ReadResult(
            title=self._extract_title(out) or f"LinkedIn Job {job_id}",
            content=out.strip(),
            url=url,
            platform="linkedin",
        )

    async def _read_jina(self, url: str) -> ReadResult:
        """Fallback: use Jina Reader."""
        try:
            resp = requests.get(
                f"https://r.jina.ai/{url}",
                headers={"Accept": "text/markdown"},
                timeout=15,
            )
            resp.raise_for_status()
            text = resp.text

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

            return ReadResult(
                title=self._extract_title(text) or url,
                content=text,
                url=url,
                platform="linkedin",
            )
        except Exception:
            return ReadResult(
                title="LinkedIn",
                content=(
                    f"⚠️ 无法读取此 LinkedIn 页面: {url}\n\n"
                    "提示：\n"
                    "- LinkedIn 需要登录才能查看大部分内容\n"
                    "- 安装 linkedin-scraper-mcp 解锁完整功能\n"
                    "- 详见 https://github.com/stickerdaniel/linkedin-mcp-server"
                ),
                url=url,
                platform="linkedin",
            )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        limit = kwargs.get("limit", 10)

        # Try MCP search first
        if _mcporter_has_linkedin():
            try:
                return await self._search_mcp(query, limit)
            except Exception as e:
                logger.warning(f"LinkedIn MCP search failed, falling back to Exa: {e}")

        # Fallback to Exa
        from agent_reach.channels.exa_search import ExaSearchChannel
        exa = ExaSearchChannel()
        return await exa.search(f"site:linkedin.com {query}", config=config, limit=limit)

    async def _search_mcp(self, query: str, limit: int) -> List[SearchResult]:
        """Search LinkedIn via MCP."""
        safe_q = query.replace('"', '\\"')
        # Try job search first (most common use case)
        try:
            out = _mcporter_call(
                f'linkedin.search_jobs(keywords: "{safe_q}")',
                timeout=60,
            )
            results = self._parse_search_results(out, "job")
            if results:
                return results[:limit]
        except Exception as e:
            logger.warning(f"LinkedIn job search MCP call failed: {e}")

        # Try people search
        try:
            out = _mcporter_call(
                f'linkedin.search_people(keywords: "{safe_q}")',
                timeout=60,
            )
            results = self._parse_search_results(out, "people")
            if results:
                return results[:limit]
        except Exception as e:
            logger.warning(f"LinkedIn people search MCP call failed: {e}")

        return []

    def _parse_search_results(self, text: str, result_type: str) -> List[SearchResult]:
        """Parse MCP search output into SearchResults.

        linkedin-scraper-mcp returns: {"url": "...", "sections": {"name": "raw text"}, "pages_visited": N}
        mcporter may output text/markdown instead of JSON.
        """
        results = []
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "sections" in data:
                raw = "\n".join(str(v) for v in data["sections"].values())
                results.append(SearchResult(
                    title=f"LinkedIn {result_type} search results",
                    url=data.get("url", ""),
                    snippet=raw[:500],
                ))
        except (json.JSONDecodeError, ValueError):
            # mcporter may output text format; wrap as a result
            if text.strip():
                results.append(SearchResult(
                    title=f"LinkedIn {result_type} search results",
                    url="",
                    snippet=text.strip()[:500],
                ))
        return results

    def _extract_title(self, text: str) -> str:
        """Extract a meaningful title from MCP/Jina output."""
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith(("{", "[", "#", "http")):
                return line[:80]
        return ""
