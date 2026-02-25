# -*- coding: utf-8 -*-
"""Twitter/X — via bird CLI (free) or Jina Reader fallback.

Backend: bird (@steipete/bird npm package) for search/timeline
         Jina Reader for single tweets
Swap to: any Twitter access tool
"""

import shutil
import subprocess
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List
import requests


def _bird_cmd():
    """Find bird CLI binary."""
    return shutil.which("bird") or shutil.which("birdx")


def _bird_env(config=None):
    """Build env dict with Twitter cookies and proxy support for bird CLI.

    Node.js native fetch() doesn't respect HTTP_PROXY/HTTPS_PROXY.
    We inject undici's EnvHttpProxyAgent via NODE_OPTIONS so bird
    automatically routes through the user's proxy.
    """
    import os
    import tempfile
    env = os.environ.copy()
    if config:
        auth_token = config.get("twitter_auth_token")
        ct0 = config.get("twitter_ct0")
        if auth_token:
            env["AUTH_TOKEN"] = auth_token
        if ct0:
            env["CT0"] = ct0

    # Auto-inject undici proxy support if HTTP_PROXY/HTTPS_PROXY is set
    has_proxy = env.get("HTTPS_PROXY") or env.get("HTTP_PROXY") or env.get("https_proxy") or env.get("http_proxy")
    if has_proxy:
        bootstrap = _get_proxy_bootstrap_path()
        if bootstrap:
            npm_root = subprocess.run(
                ["npm", "root", "-g"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
            existing_opts = env.get("NODE_OPTIONS", "")
            env["NODE_OPTIONS"] = f"--require {bootstrap} {existing_opts}".strip()
            env["NODE_PATH"] = npm_root

    return env


def _get_proxy_bootstrap_path():
    """Create/return a bootstrap JS file that sets up undici proxy for fetch."""
    import os
    import tempfile
    bootstrap_path = os.path.join(tempfile.gettempdir(), "agent-reach-undici-proxy.js")
    if not os.path.exists(bootstrap_path):
        # Check if undici is available
        npm_root = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        undici_path = os.path.join(npm_root, "undici", "index.js")
        if not os.path.exists(undici_path):
            return None
        with open(bootstrap_path, "w") as f:
            f.write(
                "try {\n"
                "  const { EnvHttpProxyAgent, setGlobalDispatcher } = require('undici');\n"
                "  if (process.env.HTTPS_PROXY || process.env.HTTP_PROXY) {\n"
                "    setGlobalDispatcher(new EnvHttpProxyAgent());\n"
                "  }\n"
                "} catch(e) {}\n"
            )
    return bootstrap_path


class TwitterChannel(Channel):
    name = "twitter"
    description = "Twitter/X 推文"
    backends = ["bird", "Jina Reader"]
    tier = 0  # Single tweet reading is zero-config

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "x.com" in domain or "twitter.com" in domain

    def check(self, config=None):
        # Basic reading always works (Jina fallback)
        bird = _bird_cmd()
        if bird:
            # Actually test bird connectivity
            try:
                result = subprocess.run(
                    [bird, "whoami"],
                    capture_output=True, timeout=15,
                    encoding='utf-8', errors='replace',
                    env=_bird_env(config),
                )
                if result.returncode == 0 and "fetch failed" not in result.stdout.lower() and "fetch failed" not in result.stderr.lower():
                    return "ok", "搜索、时间线、发推全部可用"
                else:
                    error_hint = (result.stderr or result.stdout).strip()[:100]
                    if "fetch failed" in (error_hint + result.stdout).lower():
                        return "warn", (
                            f"bird 已安装但连接失败（fetch failed）。可能原因：\n"
                            "  1. Cookie 无效或过期 → 重新导出 Cookie\n"
                            "  2. 需要代理但 Node.js fetch 不走系统代理 → 使用全局/透明代理（如 Clash TUN 模式、Proxifier）\n"
                            "  3. 网络无法直连 x.com\n"
                            "  搜索功能暂不可用，将使用 Exa 搜索作为替代"
                        )
                    return "warn", f"bird 连接异常：{error_hint}。搜索将使用 Exa 替代"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return "warn", "bird 已安装但连接超时。搜索将使用 Exa 替代"
        return "ok", "可读取推文。安装 bird + 配置 Cookie 可解锁搜索和发推"

    async def read(self, url: str, config=None) -> ReadResult:
        # Try bird first
        bird = _bird_cmd()
        if bird:
            return await self._read_bird(url, bird, config)
        # Fallback: Jina Reader
        return await self._read_jina(url)

    async def _read_bird(self, url: str, bird: str, config=None) -> ReadResult:
        result = subprocess.run(
            [bird, "read", url],
            capture_output=True, timeout=30,
            encoding='utf-8', errors='replace',
            env=_bird_env(config),
        )
        if result.returncode != 0:
            return await self._read_jina(url)

        text = result.stdout.strip()
        # Extract author from first line
        author = ""
        lines = text.split("\n")
        if lines and lines[0].startswith("@"):
            author = lines[0].split()[0]

        return ReadResult(
            title=text[:100],
            content=text,
            url=url,
            author=author,
            platform="twitter",
        )

    async def _read_jina(self, url: str) -> ReadResult:
        try:
            resp = requests.get(
                f"https://r.jina.ai/{url}",
                headers={"Accept": "text/markdown"},
                timeout=15,
            )
            resp.raise_for_status()
            text = resp.text

            # Detect unusable Jina responses for X/Twitter (JS-required pages)
            unusable_indicators = [
                "page doesn",  # "this page doesn't exist" (handles both ' and ')
                "miss what",   # "Don't miss what's happening"
                "Something went wrong. Try reloading",
                "Log in](",    # Markdown link: [Log in](...)
            ]
            if any(indicator in text for indicator in unusable_indicators):
                return ReadResult(
                    title="Twitter/X",
                    content="⚠️ Could not read this tweet.\n"
                            "The tweet may have been deleted, or the account is private.\n\n"
                            "Tips:\n"
                            "- Make sure the URL is correct\n"
                            "- Try: bird read <url> (if bird CLI is installed)\n"
                            "- For protected tweets, configure Twitter cookies: "
                            "agent-reach configure twitter-cookies AUTH_TOKEN CT0",
                    url=url,
                    platform="twitter",
                )

            title = text[:100] if text else url
            return ReadResult(
                title=title,
                content=text,
                url=url,
                platform="twitter",
            )
        except Exception:
            return ReadResult(
                title="Twitter/X",
                content="⚠️ Could not read this tweet.\n"
                        "The tweet may have been deleted, or the account is private.\n\n"
                        "Tips:\n"
                        "- Make sure the URL is correct\n"
                        "- Try: bird read <url> (if bird CLI is installed)\n"
                        "- For protected tweets, configure Twitter cookies: "
                        "agent-reach configure twitter-cookies AUTH_TOKEN CT0",
                url=url,
                platform="twitter",
            )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        limit = kwargs.get("limit", 10)

        bird = _bird_cmd()
        if bird:
            return await self._search_bird(query, limit, bird, config)

        # Fallback to Exa
        return await self._search_exa(query, limit, config)

    async def _search_bird(self, query: str, limit: int, bird: str, config=None) -> List[SearchResult]:
        try:
            result = subprocess.run(
                [bird, "search", query, "-n", str(limit)],
                capture_output=True, timeout=30,
                encoding='utf-8', errors='replace',
                env=_bird_env(config),
            )
            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                if "fetch failed" in stderr.lower() or "fetch failed" in (result.stdout or "").lower():
                    # bird can't connect — fall back to Exa silently
                    return await self._search_exa(query, limit, config)
                return await self._search_exa(query, limit, config)

            parsed = self._parse_bird_output(result.stdout)
            if not parsed:
                # bird returned nothing — try Exa
                return await self._search_exa(query, limit, config)
            return parsed
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return await self._search_exa(query, limit, config)

    def _parse_bird_output(self, text: str) -> List[SearchResult]:
        """Parse bird text output into SearchResults."""
        results = []
        current = {}
        text_lines = []

        for line in text.strip().split("\n"):
            line = line.strip()
            if line.startswith("─"):
                if current:
                    current["text"] = "\n".join(text_lines).strip()
                    results.append(SearchResult(
                        title=current.get("text", "")[:80],
                        url=current.get("url", ""),
                        snippet=current.get("text", ""),
                        author=current.get("author", ""),
                        date=current.get("date", ""),
                    ))
                    current = {}
                    text_lines = []
                continue
            if line.startswith("@") and line.endswith(":") and "(" in line:
                current["author"] = line.split()[0]
                continue
            if line.startswith("date:"):
                current["date"] = line[5:].strip()
                continue
            if line.startswith("url:"):
                current["url"] = line[4:].strip()
                continue
            if current is not None:
                text_lines.append(line)

        if current and text_lines:
            current["text"] = "\n".join(text_lines).strip()
            results.append(SearchResult(
                title=current.get("text", "")[:80],
                url=current.get("url", ""),
                snippet=current.get("text", ""),
                author=current.get("author", ""),
                date=current.get("date", ""),
            ))
        return results

    async def _search_exa(self, query: str, limit: int, config=None) -> List[SearchResult]:
        from agent_reach.channels.exa_search import ExaSearchChannel
        exa = ExaSearchChannel()
        return await exa.search(f"site:x.com {query}", config=config, limit=limit)
