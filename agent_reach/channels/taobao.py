# -*- coding: utf-8 -*-
"""Taobao/Tmall — check if taoke-mcp is available via mcporter."""

import shutil
import subprocess

from .base import Channel


class TaobaoChannel(Channel):
    name = "taobao"
    description = "淘宝/天猫商品搜索与推广"
    backends = ["taoke-mcp", "Jina Reader"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse

        d = urlparse(url).netloc.lower()
        return any(k in d for k in ("taobao.com", "tmall.com", "tb.cn"))

    def check(self, config=None):
        mcporter = shutil.which("mcporter")
        if not mcporter:
            return "off", (
                "基本内容可通过 Jina Reader 读取。完整功能需要：\n"
                "  1. npm install -g mcporter\n"
                "  2. mcporter config add taoke -- npx -y @liuliang520500/sinataoke_cn@latest\n"
                "     （需配置 TAOBAO_PID 和 TAOBAO_SESSION 环境变量）\n"
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
            "mcporter 已装但淘宝 MCP 未配置。运行：\n"
            "  mcporter config add taoke -- npx -y @liuliang520500/sinataoke_cn@latest\n"
            "  需配置环境变量：TAOBAO_PID, TAOBAO_SESSION\n"
            "  授权链接：https://oauth.taobao.com/authorize?response_type=token"
            "&client_id=34297717&state=1212&view=web"
        )
