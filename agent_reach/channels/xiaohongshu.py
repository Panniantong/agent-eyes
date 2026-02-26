# -*- coding: utf-8 -*-
"""XiaoHongShu (小红书) — via mcporter + xiaohongshu MCP server.

Backend: xiaohongshu-mcp server (internal API, reliable)
Requires: mcporter CLI + xiaohongshu MCP server running
"""

import json
import shutil
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List, Optional


class XiaoHongShuChannel(Channel):
    name = "xiaohongshu"
    description = "小红书笔记"
    backends = ["xiaohongshu-mcp"]
    tier = 2

    # ── Channel interface ──

    def can_handle(self, url: str) -> bool:
        d = urlparse(url).netloc.lower()
        return "xiaohongshu.com" in d or "xhslink.com" in d

    def check(self, config=None):
        if not shutil.which("mcporter"):
            return "off", (
                "需要 mcporter + xiaohongshu-mcp。安装步骤：\n"
                "  1. npm install -g mcporter\n"
                "  2. docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp\n"
                "  3. mcporter config add xiaohongshu http://localhost:18060/mcp\n"
                "  详见 https://github.com/xpzouying/xiaohongshu-mcp"
            )
        if not self._mcporter_has("xiaohongshu"):
            return "off", (
                "mcporter 已装但小红书 MCP 未配置。运行：\n"
                "  docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp\n"
                "  mcporter config add xiaohongshu http://localhost:18060/mcp"
            )
        try:
            out = self._mcporter_call("xiaohongshu.check_login_status()", timeout=10)
            if "已登录" in out or "logged" in out.lower():
                return "ok", "完整可用（阅读、搜索、发帖、评论、点赞）"
            return "warn", "MCP 已连接但未登录，需扫码登录"
        except Exception:
            return "warn", "MCP 连接异常，检查 xiaohongshu-mcp 服务是否在运行"

    async def read(self, url: str, config=None) -> ReadResult:
        if not self._mcporter_has("xiaohongshu"):
            return ReadResult(
                title="XiaoHongShu",
                content=(
                    "⚠️ 小红书需要 mcporter + xiaohongshu-mcp 才能使用。\n\n"
                    "安装步骤：\n"
                    "1. npm install -g mcporter\n"
                    "2. docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp\n"
                    "3. mcporter config add xiaohongshu http://localhost:18060/mcp\n"
                    "4. 运行 agent-reach doctor 检查状态\n\n"
                    "详见 https://github.com/xpzouying/xiaohongshu-mcp"
                ),
                url=url, platform="xiaohongshu",
            )

        note_id = self._extract_note_id(url)
        if not note_id:
            return ReadResult(
                title="XiaoHongShu",
                content=f"⚠️ 无法从 URL 提取笔记 ID: {url}",
                url=url, platform="xiaohongshu",
            )

        # Step 1: get xsec_token from feeds
        xsec_token = self._find_token(note_id)

        if not xsec_token:
            return ReadResult(
                title="XiaoHongShu",
                content=(
                    f"⚠️ 无法获取笔记 {note_id} 的访问令牌。\n"
                    "小红书需要 xsec_token 才能读取笔记详情。\n"
                    "请先通过搜索找到这篇笔记，或直接使用搜索功能。"
                ),
                url=url, platform="xiaohongshu",
            )

        # Step 2: get detail
        out = self._mcporter_call(
            f'xiaohongshu.get_feed_detail(feed_id: "{note_id}", xsec_token: "{xsec_token}")',
            timeout=15,
        )

        return ReadResult(
            title=self._extract_first_line(out) or f"XHS {note_id}",
            content=out.strip(),
            url=url, platform="xiaohongshu",
        )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        if not self._mcporter_has("xiaohongshu"):
            raise ValueError(
                "小红书搜索需要 mcporter + xiaohongshu-mcp。\n"
                "安装: npm install -g mcporter && mcporter config add xiaohongshu http://localhost:18060/mcp"
            )
        limit = kwargs.get("limit", 10)
        safe_q = query.replace('"', '\\"')
        out = self._mcporter_call(f'xiaohongshu.search_feeds(keyword: "{safe_q}")', timeout=30)

        results = []
        try:
            data = json.loads(out)
            for item in data.get("feeds", [])[:limit]:
                card = item.get("noteCard", {})
                user = card.get("user", {})
                interact = card.get("interactInfo", {})
                results.append(SearchResult(
                    title=card.get("displayTitle", ""),
                    url=f"https://www.xiaohongshu.com/explore/{item.get('id', '')}",
                    snippet=f"👤 {user.get('nickname', '')} · ❤ {interact.get('likedCount', '0')}",
                    score=0,
                ))
        except (json.JSONDecodeError, KeyError):
            pass
        return results

    # ── Helpers ──

    def _extract_note_id(self, url: str) -> str:
        parts = urlparse(url).path.strip("/").split("/")
        return parts[-1] if parts else ""

    def _find_token(self, note_id: str) -> Optional[str]:
        """Try to find xsec_token for a note from feeds."""
        try:
            out = self._mcporter_call("xiaohongshu.list_feeds()", timeout=15)
            data = json.loads(out)
            for feed in data.get("feeds", []):
                if feed.get("id") == note_id:
                    return feed.get("xsecToken", "")
        except Exception:
            pass
        return None
