# -*- coding: utf-8 -*-
"""Boss直聘 (BOSS Zhipin) — via mcp-bosszp (MCP) or Jina Reader fallback.

Backend: mcp-bosszp (161 stars, FastMCP + Playwright)
Swap to: any Boss直聘 access tool
"""

import json
import logging
import shutil
import subprocess
import time
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List

logger = logging.getLogger(__name__)

# Module-level cache for MCP availability
_mcp_cache = {"available": None, "checked_at": 0, "server_name": "bosszhipin"}


def _mcporter_has_bosszhipin() -> bool:
    """Check if mcporter has Boss直聘 MCP configured (cached 60s)."""
    if time.time() - _mcp_cache["checked_at"] < 60:
        return _mcp_cache["available"]

    if not shutil.which("mcporter"):
        _mcp_cache["available"] = False
        _mcp_cache["checked_at"] = time.time()
        return False
    try:
        r = subprocess.run(
            ["mcporter", "list"], capture_output=True, text=True, timeout=10
        )
        out = r.stdout.lower()
        available = "boss" in out or "zhipin" in out or "bosszhipin" in out
        _mcp_cache["available"] = available
        _mcp_cache["checked_at"] = time.time()

        # Also detect server name
        if available:
            for line in r.stdout.split("\n"):
                line_lower = line.strip().lower()
                for name in ["bosszhipin", "boss-zp", "bosszp", "boss"]:
                    if name in line_lower:
                        parts = line.strip().split()
                        if parts:
                            _mcp_cache["server_name"] = parts[0]
                        break
        return available
    except Exception:
        _mcp_cache["available"] = False
        _mcp_cache["checked_at"] = time.time()
        return False


def _mcporter_call(expr: str, timeout: int = 30) -> str:
    """Call a Boss直聘 MCP tool via mcporter."""
    r = subprocess.run(
        ["mcporter", "call", expr],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout)
    return r.stdout


class BossZhipinChannel(Channel):
    name = "bosszhipin"
    description = "Boss直聘职位搜索"
    backends = ["mcp-bosszp", "Jina Reader"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "zhipin.com" in domain or "boss.com" in domain

    def check(self, config=None):
        if _mcporter_has_bosszhipin():
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
        return await self._read_jina(url)

    async def _read_jina(self, url: str) -> ReadResult:
        """Read Boss直聘 page via Jina Reader."""
        import requests
        try:
            resp = requests.get(
                f"https://r.jina.ai/{url}",
                headers={"Accept": "text/markdown"},
                timeout=15,
            )
            resp.raise_for_status()
            text = resp.text

            if len(text.strip()) < 50:
                return ReadResult(
                    title="Boss直聘",
                    content=(
                        f"⚠️ 无法读取此页面内容: {url}\n\n"
                        "提示：\n"
                        "- 安装 mcp-bosszp 可解锁职位搜索和自动打招呼\n"
                        "- 详见 https://github.com/mucsbr/mcp-bosszp"
                    ),
                    url=url, platform="bosszhipin",
                )

            # Extract title from first meaningful line
            title = url
            for line in text.split("\n"):
                line = line.strip()
                if line and not line.startswith(("#", "http", "![", "[")):
                    title = line[:80]
                    break

            return ReadResult(
                title=title, content=text,
                url=url, platform="bosszhipin",
            )
        except Exception as e:
            logger.warning(f"Boss直聘 Jina Reader failed: {e}")
            return ReadResult(
                title="Boss直聘",
                content=(
                    f"⚠️ 无法读取此 Boss直聘页面: {url}\n\n"
                    "提示：\n"
                    "- Boss直聘部分页面需要登录\n"
                    "- 安装 mcp-bosszp 可解锁完整功能\n"
                    "- 详见 https://github.com/mucsbr/mcp-bosszp"
                ),
                url=url, platform="bosszhipin",
            )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        limit = kwargs.get("limit", 10)

        # Try MCP search first
        if _mcporter_has_bosszhipin():
            try:
                return await self._search_mcp(query, limit, config)
            except Exception as e:
                logger.warning(f"Boss直聘 MCP search failed, falling back to Exa: {e}")

        # Fallback to Exa
        from agent_reach.channels.exa_search import ExaSearchChannel
        exa = ExaSearchChannel()
        return await exa.search(f"site:zhipin.com {query}", config=config, limit=limit)

    async def _search_mcp(self, query: str, limit: int, config=None) -> List[SearchResult]:
        """Search Boss直聘 via MCP.

        Note: mcp-bosszp only supports get_recommend_jobs_tool (no keyword search).
        We extract filter params (salary, experience, job_type) from the query.
        """
        server = _mcp_cache.get("server_name", "bosszhipin")

        # Parse query for known filter keywords
        params = ["page: 1"]
        query_lower = query.lower()

        # Experience mapping
        exp_map = {
            "应届": "应届生", "在校": "在校生", "实习": "在校生",
            "1年": "一年以内", "一年": "一年以内",
            "1-3年": "一到三年", "一到三年": "一到三年",
            "3-5年": "三到五年", "三到五年": "三到五年",
            "5-10年": "五到十年", "五到十年": "五到十年",
            "10年": "十年以上", "十年以上": "十年以上",
        }
        for key, val in exp_map.items():
            if key in query_lower:
                params.append(f'experience: "{val}"')
                break

        # Salary mapping
        salary_map = {
            "3k以下": "3k以下", "3-5k": "3-5k", "5-10k": "5-10k",
            "10-20k": "10-20k", "20-50k": "20-50k", "50k": "50以上",
        }
        for key, val in salary_map.items():
            if key in query_lower:
                params.append(f'salary: "{val}"')
                break

        # Job type
        if "兼职" in query_lower:
            params.append('job_type: "兼职"')
        elif "全职" in query_lower:
            params.append('job_type: "全职"')

        param_str = ", ".join(params)
        out = _mcporter_call(
            f'{server}.get_recommend_jobs_tool({param_str})',
            timeout=30,
        )
        results = self._parse_jobs(out, limit)
        if not results:
            raise ValueError("No results from MCP")
        return results

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
                        title=title, url=url, snippet=snippet,
                    ))
        except (json.JSONDecodeError, KeyError):
            pass
        return results
