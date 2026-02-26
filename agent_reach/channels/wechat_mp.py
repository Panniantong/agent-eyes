# -*- coding: utf-8 -*-
"""WeChat Official Account (微信公众号) — check if mcporter + wechat-official-account-mcp is available."""

import shutil
import subprocess
from .base import Channel


class WechatMPChannel(Channel):
    name = "wechat-mp"
    description = "微信公众号"
    backends = ["wechat-official-account-mcp"]
    tier = 2

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "mp.weixin.qq.com" in d

    def check(self, config=None):
        if not shutil.which("mcporter"):
            return "off", (
                "需要 mcporter + wechat-official-account-mcp。安装步骤：\n"
                "  1. npm install -g mcporter\n"
                "  2. npm install -g wechat-official-account-mcp\n"
                "  3. mcporter config add wechat-mp --stdio "
                "\"wechat-mcp mcp -a <APP_ID> -s <APP_SECRET>\"\n"
                "  详见 https://github.com/xwang152-jack/wechat-official-account-mcp"
            )
        try:
            r = subprocess.run(
                ["mcporter", "list"], capture_output=True, text=True, timeout=10
            )
            if "wechat" not in r.stdout:
                return "off", (
                    "mcporter 已装但微信公众号 MCP 未配置。运行：\n"
                    "  npm install -g wechat-official-account-mcp\n"
                    "  mcporter config add wechat-mp --stdio "
                    "\"wechat-mcp mcp -a <APP_ID> -s <APP_SECRET>\"\n"
                    "  需要微信公众号后台的 AppID 和 AppSecret"
                )
        except Exception:
            return "off", "mcporter 连接异常"
        try:
            r = subprocess.run(
                ["mcporter", "call",
                 "wechat-mp.wechat_auth(action: \"get_config\")"],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode == 0 and "error" not in r.stdout.lower():
                return "ok", "完整可用（草稿、发布、素材、用户、统计、消息管理）"
            return "warn", (
                "MCP 已连接但认证异常，请检查 AppID/AppSecret 是否正确"
            )
        except Exception:
            return "warn", "MCP 连接异常，检查 wechat-mcp 服务是否在运行"
