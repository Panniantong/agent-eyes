# -*- coding: utf-8 -*-
"""Exa semantic search — via mcporter + Exa MCP server.

Backend: Exa MCP at mcp.exa.ai (OAuth, no API key needed)
Requires: mcporter CLI
"""

import json
import shutil
from .base import Channel, SearchResult
from typing import List


class ExaSearchChannel(Channel):
    name = "exa_search"
    description = "全网语义搜索（同时支持 Reddit/Twitter 搜索）"
    backends = ["exa-mcp"]
    tier = 1

    # ── Channel interface ──

    def can_handle(self, url: str) -> bool:
        return False  # search-only

    async def read(self, url: str, config=None):
        raise NotImplementedError("Exa is a search engine, not a reader")

    def check(self, config=None):
        if not shutil.which("mcporter"):
            return "off", (
                "需要 mcporter。安装：npm install -g mcporter && "
                "mcporter config add exa https://mcp.exa.ai/mcp"
            )
        if not self._mcporter_has("exa"):
            return "off", "mcporter 已装但 Exa 未配置。运行：mcporter config add exa https://mcp.exa.ai/mcp"
        return "ok", "MCP 已连接，免 Key 直接可用（全网搜索 + Reddit + Twitter）"

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        if not self._mcporter_has("exa"):
            raise ValueError(
                "Exa 搜索需要 mcporter。安装：\n"
                "  npm install -g mcporter\n"
                "  mcporter config add exa https://mcp.exa.ai/mcp"
            )

        limit = kwargs.get("limit", 5)
        safe_q = query.replace('"', '\\"')
        out = self._mcporter_call(
            f'exa.web_search_exa(query: "{safe_q}", numResults: {min(limit, 10)})',
            timeout=30,
        )
        return self._parse_output(out, limit)

    # ── Parse mcporter text output ──

    def _parse_output(self, text: str, limit: int) -> List[SearchResult]:
        """Parse mcporter's Title/URL/Text block format."""
        results = []
        cur = {}

        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("Title: "):
                if cur.get("title"):
                    results.append(self._make_result(cur))
                cur = {"title": line[7:]}
            elif line.startswith("URL: "):
                cur["url"] = line[5:]
            elif line.startswith("Published Date: "):
                cur["date"] = line[16:]
            elif line.startswith("Text: "):
                cur["text"] = line[6:]
            elif "text" in cur and line:
                cur["text"] += " " + line

        if cur.get("title"):
            results.append(self._make_result(cur))

        return results[:limit]

    @staticmethod
    def _make_result(d: dict) -> SearchResult:
        return SearchResult(
            title=d.get("title", ""),
            url=d.get("url", ""),
            snippet=d.get("text", "")[:500],
            date=d.get("date", ""),
            score=0,
        )
