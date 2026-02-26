# -*- coding: utf-8 -*-
"""Boss直聘 (BOSS Zhipin) — via mcp-bosszp (MCP) or Jina Reader fallback.

Backend: mcp-bosszp (161 stars, FastMCP + Playwright)
Swap to: any Boss直聘 access tool
"""

import json
import subprocess
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List


def _get_mcp_name() -> str:
    """Get the actual MCP server name configured in mcporter."""
    try:
        r = subprocess.run(
            ["mcporter", "list"], capture_output=True, text=True, timeout=10
        )
        for line in r.stdout.split("\n"):
            line_lower = line.strip().lower()
            for name in ["bosszhipin", "boss-zp", "bosszp", "boss"]:
                if name in line_lower:
                    # Extract the actual server name
                    parts = line.strip().split()
                    if parts:
                        return parts[0]
        return "bosszhipin"
    except Exception:
        return "bosszhipin"


class BossZhipinChannel(Channel):
    name = "bosszhipin"
    description = "Boss直聘职位搜索"
    backends = ["mcp-bosszp", "Jina Reader"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "zhipin.com" in domain or "boss.com" in domain

    def check(self, config=None):
        if self._mcporter_has("boss"):
            return "ok", "可搜索职位、向 HR 打招呼"

        return "off", (
            "可通过 Jina Reader 读取职位页面。完整功能需要：\n"
            "  1. git clone https://github.com/mucsbr/mcp-bosszp.git\n"
            "  2. cd mcp-bosszp && pip install -r requirements.txt && playwright install chromium\n"
            "  3. python boss_zhipin_fastmcp_v2.py（启动后扫码登录）\n"
            "  4. mcporter config add bosszhipin http://localhost:8000/mcp\n"
            "  或用 Docker：docker-compose up -d\n"
            "  详见 https://github.com/mucsbr/mcp-bosszp"
        )

    async def read(self, url: str, config=None) -> ReadResult:
        # Boss直聘 pages mostly work with Jina Reader
        return await self._jina_read(
            url, "bosszhipin",
            error_hint=(
                f"⚠️ 无法读取此 Boss直聘页面: {url}\n\n"
                "提示：\n"
                "- Boss直聘部分页面需要登录\n"
                "- 安装 mcp-bosszp 可解锁完整功能\n"
                "- 详见 https://github.com/mucsbr/mcp-bosszp"
            ),
        )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        limit = kwargs.get("limit", 10)

        # Try MCP search first
        if self._mcporter_has("boss"):
            try:
                return await self._search_mcp(query, limit, config)
            except Exception:
                pass

        # Fallback to Exa
        from agent_reach.channels.exa_search import ExaSearchChannel
        exa = ExaSearchChannel()
        return await exa.search(f"site:zhipin.com {query}", config=config, limit=limit)

    async def _search_mcp(self, query: str, limit: int, config=None) -> List[SearchResult]:
        """Search Boss直聘 via MCP."""
        server = _get_mcp_name()
        try:
            out = self._mcporter_call(
                f'{server}.get_recommend_jobs_tool(page: 1)',
                timeout=30,
            )
            return self._parse_jobs(out, limit)
        except Exception:
            return []

    def _parse_jobs(self, text: str, limit: int) -> List[SearchResult]:
        """Parse MCP job search output into SearchResults."""
        results = []
        try:
            data = json.loads(text)
            jobs = data if isinstance(data, list) else data.get("jobs", data.get("results", []))
            for job in jobs[:limit]:
                if isinstance(job, dict):
                    title = job.get("title") or job.get("jobName", "")
                    company = job.get("company") or job.get("brandName", "")
                    salary = job.get("salary") or job.get("salaryDesc", "")
                    url = job.get("url", "")
                    snippet = f"🏢 {company}" if company else ""
                    if salary:
                        snippet += f" · 💰 {salary}"
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                    ))
        except (json.JSONDecodeError, KeyError):
            pass
        return results
