# -*- coding: utf-8 -*-
"""Twitter/X — check if xreach CLI is available."""

import shutil
import subprocess
from .base import Channel

# Minimum xreach-cli version with longform tweet and X Article support.
# v0.3.2 added: extractTweetText() preferring note_tweet for long tweets (#aad6a16)
# and X Article URL support (/article/ path, #2e05825).
_MIN_XREACH_VERSION = (0, 3, 2)


def _parse_version(ver_str: str) -> tuple[int, ...]:
    """Parse a semver string like '0.3.2' into a tuple (0, 3, 2)."""
    try:
        return tuple(int(x) for x in ver_str.strip().split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


class TwitterChannel(Channel):
    name = "twitter"
    description = "Twitter/X 推文"
    backends = ["xreach CLI"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "x.com" in d or "twitter.com" in d

    def check(self, config=None):
        xreach = shutil.which("xreach")
        if not xreach:
            return "warn", (
                "xreach CLI 未安装。搜索可通过 Exa 替代。安装：\n"
                "  npm install -g xreach-cli"
            )
        # Check version — longform tweet support requires >= 0.3.2
        try:
            ver_result = subprocess.run(
                [xreach, "--version"], capture_output=True,
                encoding="utf-8", errors="replace", timeout=5
            )
            version_str = (ver_result.stdout or ver_result.stderr).strip()
            version_tuple = _parse_version(version_str)
            if version_tuple < _MIN_XREACH_VERSION:
                min_str = ".".join(str(x) for x in _MIN_XREACH_VERSION)
                return "warn", (
                    f"xreach CLI 版本过旧（当前 {version_str}，需 >= {min_str}）。"
                    f"旧版本无法读取长文推文（note_tweet）和 X Article。升级：\n"
                    f"  npm install -g xreach-cli@latest"
                )
        except Exception:
            pass  # version check failure is non-fatal; proceed to auth check

        try:
            r = subprocess.run(
                [xreach, "auth", "check"], capture_output=True,
                encoding="utf-8", errors="replace", timeout=10
            )
            if r.returncode == 0:
                return "ok", "完整可用（读取、搜索推文，含长文/X Article）"
            return "warn", (
                "xreach CLI 已安装但未配置 Cookie。运行：\n"
                "  agent-reach configure twitter-cookies \"auth_token=xxx; ct0=yyy\""
            )
        except Exception:
            return "warn", "xreach CLI 已安装但连接失败"
