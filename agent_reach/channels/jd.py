# -*- coding: utf-8 -*-
"""JD.com — check if taoke-mcp is available via mcporter."""

import shutil
import subprocess

from .base import Channel


class JDChannel(Channel):
    name = "jd"
    description = "京东商品搜索与推广"
    backends = ["taoke-mcp", "Jina Reader"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse

        d = urlparse(url).netloc.lower()
        return any(k in d for k in ("jd.com", "jd.hk", "3.cn"))

    def check(self, config=None):
        mcporter = shutil.which("mcporter")
        if not mcporter:
            return "off", (
                "基本内容可通过 Jina Reader 读取。完整功能需要：\n"
                "  1. npm install -g mcporter\n"
                "  2. mcporter config add taoke -- npx -y @liuliang520500/sinataoke_cn@latest\n"
                "     （需配置 JD_KEY 和 JD_PID 环境变量）\n"
                "  详见 https://github.com/liuliang520530/taoke-mcp"
            )
        try:
            r = subprocess.run(
                [mcporter, "config", "list"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            if "taoke" in r.stdout.lower():
                return "ok", "可搜索商品、转链、查订单（通过 taoke-mcp）"
        except Exception:
            pass
        return "off", (
            "mcporter 已装但京东 MCP 未配置。运行：\n"
            "  mcporter config add taoke -- npx -y @liuliang520500/sinataoke_cn@latest\n"
            "  需配置环境变量：JD_KEY, JD_PID\n"
            "  在 union.jd.com 后台获取"
        )
