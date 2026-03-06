# -*- coding: utf-8 -*-
"""Amazon — product search and details via Jina Reader."""

import subprocess
from .base import Channel


class AmazonChannel(Channel):
    name = "amazon"
    description = "Amazon 商品搜索与详情"
    backends = ["Jina Reader"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "amazon." in d

    def check(self, config=None):
        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "https://r.jina.ai/https://www.amazon.com/dp/B0D1XD1ZV3",
                 "--connect-timeout", "10"],
                capture_output=True, encoding="utf-8", timeout=15,
            )
            if r.stdout.strip() == "200":
                return "ok", "Amazon 商品搜索与详情可用（通过 Jina Reader，免费无需 API Key）"
            return "warn", f"Jina Reader 返回 HTTP {r.stdout.strip()}"
        except Exception as e:
            return "warn", f"Jina Reader 连接失败：{e}"
