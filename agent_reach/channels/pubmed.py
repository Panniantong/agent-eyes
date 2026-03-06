# -*- coding: utf-8 -*-
"""PubMed — biomedical literature search via NCBI Entrez API."""

import requests
from .base import Channel


class PubMedChannel(Channel):
    name = "pubmed"
    description = "PubMed 生物医学文献"
    backends = ["NCBI Entrez API"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "pubmed.ncbi.nlm.nih.gov" in d or "ncbi.nlm.nih.gov" in d

    def check(self, config=None):
        try:
            params = {
                "db": "pubmed",
                "term": "test",
                "retmax": "1",
                "retmode": "json",
            }
            api_key = config.get("ncbi_api_key") if config else None
            if api_key:
                params["api_key"] = api_key
            r = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params=params,
                timeout=5,
            )
            if r.status_code == 200:
                data = r.json()
                count = data.get("esearchresult", {}).get("count", "0")
                msg = f"PubMed Entrez API 可用（{count}+ 篇文献可检索）"
                if api_key:
                    msg += "，API Key 已配置（10次/秒）"
                else:
                    msg += "。可选：配置 NCBI API Key 提升速率（3→10次/秒）"
                return "ok", msg
            return "warn", f"PubMed API 返回异常（HTTP {r.status_code}）"
        except requests.exceptions.Timeout:
            return "warn", "PubMed API 连接超时，可能需要代理"
        except Exception as e:
            return "warn", f"PubMed API 连接失败：{e}"
