# -*- coding: utf-8 -*-
"""Web pages — via Jina Reader API (free, no config needed).

Backend: Jina Reader (https://r.jina.ai)
Swap to: Firecrawl, Trafilatura, or any other reader API
"""

import httpx
from loguru import logger
from .base import Channel, ReadResult


class WebChannel(Channel):
    name = "web"
    description = "网页（任意 URL）"
    backends = ["Jina Reader API"]
    tier = 0

    JINA_URL = "https://r.jina.ai/"

    def can_handle(self, url: str) -> bool:
        # Fallback — handles any URL not matched by other channels
        return True

    async def read(self, url: str, config=None) -> ReadResult:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.JINA_URL}{url}",
                    headers={"Accept": "text/markdown"},
                )
                resp.raise_for_status()
                text = resp.text

            # Extract title from first markdown heading
            title = url
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
                if line.startswith("Title:"):
                    title = line[6:].strip()
                    break

            return ReadResult(
                title=title,
                content=text,
                url=url,
                platform="web",
            )
        except Exception as e:
            logger.debug(f"WebChannel read failed for {url}: {e}")
            return ReadResult(
                title=url,
                content=f"⚠️ 无法读取网页: {url}\n\n{e}",
                url=url,
                platform="web",
            )
