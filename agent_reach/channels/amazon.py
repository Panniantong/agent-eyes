# -*- coding: utf-8 -*-
"""Amazon — check if mcp-server-amazon is available via mcporter."""

import shutil
import subprocess

from .base import Channel


class AmazonChannel(Channel):
    name = "amazon"
    description = "亚马逊商品搜索与详情"
    backends = ["mcp-server-amazon", "Jina Reader"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse

        d = urlparse(url).netloc.lower()
        return "amazon." in d or "amzn." in d

    def check(self, config=None):
        mcporter = shutil.which("mcporter")
        if not mcporter:
            return "off", (
                "基本内容可通过 Jina Reader 读取。完整功能需要：\n"
                "  1. npm install -g mcporter\n"
                "  2. mcporter config add amazon -- npx -y mcp-server-amazon\n"
                "  详见 https://github.com/rigwild/mcp-server-amazon"
            )
        try:
            r = subprocess.run(
                [mcporter, "config", "list"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            if "amazon" in r.stdout.lower():
                return "ok", "可搜索商品、查看详情、管理购物车（通过 mcp-server-amazon）"
        except Exception:
            pass
        return "off", (
            "mcporter 已装但 Amazon MCP 未配置。运行：\n"
            "  mcporter config add amazon -- npx -y mcp-server-amazon"
        )
