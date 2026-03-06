# -*- coding: utf-8 -*-
"""arXiv — academic preprint search and reading via arXiv API."""

import requests
from .base import Channel


class ArxivChannel(Channel):
    name = "arxiv"
    description = "arXiv 学术预印本"
    backends = ["arXiv API"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "arxiv.org" in d

    def check(self, config=None):
        try:
            r = requests.get(
                "http://export.arxiv.org/api/query",
                params={"search_query": "test", "max_results": "1"},
                timeout=5,
            )
            if r.status_code == 200 and "<entry>" in r.text:
                return "ok", "arXiv API 可用（搜索、读取论文元数据）"
            return "warn", f"arXiv API 返回异常（HTTP {r.status_code}）"
        except requests.exceptions.Timeout:
            return "warn", "arXiv API 连接超时，可能需要代理"
        except Exception as e:
            return "warn", f"arXiv API 连接失败：{e}"
