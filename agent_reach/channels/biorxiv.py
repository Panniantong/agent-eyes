# -*- coding: utf-8 -*-
"""bioRxiv / medRxiv — biology and medical preprints via bioRxiv API."""

import requests
from .base import Channel


class BiorxivChannel(Channel):
    name = "biorxiv"
    description = "bioRxiv / medRxiv 生物医学预印本"
    backends = ["bioRxiv API"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "biorxiv.org" in d or "medrxiv.org" in d

    def check(self, config=None):
        try:
            r = requests.get(
                "https://api.biorxiv.org/details/biorxiv/2026-01-01/2026-01-02/0/1",
                timeout=5,
            )
            if r.status_code == 200:
                data = r.json()
                if "collection" in data:
                    return "ok", "bioRxiv / medRxiv API 可用（按日期检索预印本）"
                return "ok", "bioRxiv API 可达"
            return "warn", f"bioRxiv API 返回异常（HTTP {r.status_code}）"
        except requests.exceptions.Timeout:
            return "warn", "bioRxiv API 连接超时，可能需要代理"
        except Exception as e:
            return "warn", f"bioRxiv API 连接失败：{e}"
