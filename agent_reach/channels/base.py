# -*- coding: utf-8 -*-
"""
Channel base class — the universal interface for all platforms.

Every channel (YouTube, Twitter, GitHub, etc.) implements this interface.
The backend tool can be swapped anytime without changing anything else.

Example:
    class YouTubeChannel(Channel):
        name = "youtube"
        backends = ["yt-dlp"]  # current backend, can be swapped
        
        async def read(self, url, config):
            # Just call yt-dlp, return standardized dict
            ...
"""

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ReadResult:
    """Standardized read result. Every channel returns this."""
    title: str
    content: str
    url: str
    author: str = ""
    date: str = ""
    platform: str = ""
    extra: dict = None

    def __post_init__(self):
        self.extra = self.extra or {}

    def to_dict(self) -> dict:
        d = {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "platform": self.platform,
        }
        if self.author:
            d["author"] = self.author
        if self.date:
            d["date"] = self.date
        if self.extra:
            d["extra"] = self.extra
        return d


@dataclass
class SearchResult:
    """Standardized search result."""
    title: str
    url: str
    snippet: str = ""
    author: str = ""
    date: str = ""
    score: float = 0
    extra: dict = None

    def __post_init__(self):
        self.extra = self.extra or {}

    def to_dict(self) -> dict:
        d = {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
        }
        if self.author:
            d["author"] = self.author
        if self.date:
            d["date"] = self.date
        if self.extra:
            d["extra"] = self.extra
        return d


class Channel(ABC):
    """
    Base class for all channels.
    
    Subclasses just need to implement:
    - read(url, config) → ReadResult
    - can_handle(url) → bool
    - check(config) → (status, message)
    
    Optionally:
    - search(query, config, **kwargs) → list[SearchResult]
    """

    name: str = ""                    # e.g. "youtube"
    description: str = ""             # e.g. "YouTube video transcripts"
    backends: List[str] = []          # e.g. ["yt-dlp"] — what external tool is used
    requires_config: List[str] = []   # e.g. ["reddit_proxy"]
    requires_tools: List[str] = []    # e.g. ["yt-dlp"]
    tier: int = 0                     # 0=zero-config, 1=needs free key, 2=needs setup

    @abstractmethod
    async def read(self, url: str, config=None) -> ReadResult:
        """Read content from a URL. Must return ReadResult."""
        ...

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this channel can handle this URL."""
        ...

    def check(self, config=None) -> Tuple[str, str]:
        """
        Check if this channel is available.
        Returns (status, message) where status is 'ok'/'warn'/'off'/'error'.
        """
        # Check required tools
        for tool in self.requires_tools:
            if not shutil.which(tool):
                return "off", f"需要安装：pip install {tool}"

        # Check required config
        for key in self.requires_config:
            if config and not config.get(key):
                return "off", f"需要配置 {key}，运行 agent-reach setup"

        return "ok", f"{'、'.join(self.backends) if self.backends else '内置'}"

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        """Search this platform. Override if supported."""
        raise NotImplementedError(f"{self.name} does not support search")

    def can_search(self) -> bool:
        """Whether this channel supports search."""
        try:
            # Check if search is overridden
            return type(self).search is not Channel.search
        except Exception:
            return False

    async def _jina_read(self, url: str, platform: str, error_hint: str = "") -> "ReadResult":
        """通用 Jina Reader fallback，带 debug 日志。"""
        import httpx
        from loguru import logger
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://r.jina.ai/{url}",
                    headers={"Accept": "text/markdown"},
                )
                resp.raise_for_status()
                text = resp.text
                return ReadResult(
                    title=text[:100] if text else url,
                    content=text, url=url, platform=platform,
                )
        except Exception as e:
            logger.debug(f"Jina Reader failed for {url}: {e}")
            return ReadResult(
                title=platform.capitalize(),
                content=error_hint or f"⚠️ 无法读取: {url}",
                url=url, platform=platform,
            )

    def _mcporter_has(self, server_name: str) -> bool:
        """检查 mcporter 是否配置了指定 server。"""
        import shutil as _shutil
        import subprocess as _subprocess
        if not _shutil.which("mcporter"):
            return False
        try:
            r = _subprocess.run(["mcporter", "list"], capture_output=True, text=True, timeout=10)
            return server_name.lower() in r.stdout.lower()
        except Exception:
            return False

    def _mcporter_call(self, expr: str, timeout: int = 30) -> str:
        """通过 mcporter 调用 MCP 工具。失败时抛 RuntimeError。"""
        import subprocess as _subprocess
        r = _subprocess.run(["mcporter", "call", expr], capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(r.stderr or r.stdout)
        return r.stdout

    @staticmethod
    def _extract_first_line(text: str) -> str:
        """从文本中提取第一行有效内容作为标题（最多 80 字符）。"""
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith(("{", "[", "#", "http")):
                return line[:80]
        return ""
