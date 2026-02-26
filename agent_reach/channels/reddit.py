# -*- coding: utf-8 -*-
"""Reddit — via Reddit JSON API + optional proxy.

Backend: Reddit public JSON API (append .json to any URL)
Swap to: any Reddit access method
"""

import json
import os
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse
from .base import Channel, ReadResult


class RedditChannel(Channel):
    name = "reddit"
    description = "Reddit 帖子和评论"
    backends = ["Reddit JSON API"]
    tier = 2

    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "reddit.com" in domain or "redd.it" in domain

    def check(self, config=None):
        proxy = config.get("reddit_proxy") if config else None
        has_bot = bool(os.environ.get("REDDIT_CLIENT_ID"))
        if proxy and has_bot:
            return "ok", "完整可用（代理 + OAuth Bot）"
        elif proxy:
            return "ok", "代理已配置，可读取帖子。配置 REDDIT_CLIENT_ID/SECRET 可解锁高级搜索和发帖"
        elif has_bot:
            return "warn", "OAuth Bot 已配置，但服务器直连可能被封。配个代理更稳定：agent-reach configure proxy URL"
        else:
            return "off", "搜索用 Exa 免费可用。读帖子需配个代理：agent-reach configure proxy URL"

    async def read(self, url: str, config=None) -> ReadResult:
        proxy = config.get("reddit_proxy") if config else None
        proxies = {"http": proxy, "https": proxy} if proxy else None

        parsed = urlparse(url)

        # Fix #1: Resolve redd.it short links via HEAD redirect
        if "redd.it" in parsed.netloc:
            try:
                head_resp = requests.head(
                    url,
                    allow_redirects=True,
                    timeout=10,
                    headers={"User-Agent": self.USER_AGENT},
                    proxies=proxies,
                )
                url = head_resp.url
                parsed = urlparse(url)
            except Exception:
                pass  # Fall through with original URL; may 404

        # Clean URL: remove query params, trailing slash, then add .json
        clean_path = parsed.path.rstrip("/")
        # Remove trailing .json if already present (avoid double .json)
        if clean_path.endswith(".json"):
            clean_path = clean_path[:-5]
        json_url = f"https://www.reddit.com{clean_path}.json"

        # Fix #5: Catch network-level exceptions
        try:
            resp = requests.get(
                json_url,
                headers={"User-Agent": self.USER_AGENT},
                proxies=proxies,
                params={"limit": 50},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            return ReadResult(
                title="Reddit",
                content="⚠️ 无法连接到 Reddit，请检查网络或代理配置。",
                url=url,
                platform="reddit",
            )
        except requests.exceptions.Timeout:
            return ReadResult(
                title="Reddit",
                content="⚠️ 请求 Reddit 超时，请稍后重试或检查代理。",
                url=url,
                platform="reddit",
            )
        except requests.exceptions.ProxyError:
            return ReadResult(
                title="Reddit",
                content="⚠️ 代理连接失败，请检查代理地址和凭证。",
                url=url,
                platform="reddit",
            )
        except requests.exceptions.RequestException as e:
            return ReadResult(
                title="Reddit",
                content=f"⚠️ 请求失败: {e}",
                url=url,
                platform="reddit",
            )

        # Fix #4: Friendly errors for all HTTP status codes
        if resp.status_code != 200:
            if resp.status_code in (403, 429):
                return ReadResult(
                    title="Reddit",
                    content="⚠️ Reddit blocked this request (403 Forbidden). "
                            "Reddit blocks most server IPs.\n"
                            "Fix: agent-reach configure proxy http://user:pass@ip:port\n"
                            "Cheap option: https://www.webshare.io ($1/month)\n\n"
                            "Alternatively, search Reddit via Exa (free, no proxy needed): "
                            "agent-reach search-reddit \"your query\"",
                    url=url,
                    platform="reddit",
                )
            return ReadResult(
                title="Reddit",
                content=f"⚠️ Reddit 返回 HTTP {resp.status_code}: {url}",
                url=url,
                platform="reddit",
            )

        # Fix #2: Safe JSON parsing
        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError):
            return ReadResult(
                title="Reddit",
                content=f"⚠️ Reddit 返回了非 JSON 响应: {url}",
                url=url,
                platform="reddit",
            )

        # Subreddit listing page: /r/sub/, /r/sub/hot, /r/sub/new, /r/sub/top
        if isinstance(data, dict) and data.get("kind") == "Listing":
            return self._parse_listing(data, url)

        if isinstance(data, list) and len(data) >= 1:
            # Fix #2 continued: Safe nested access
            children = data[0].get("data", {}).get("children", [])
            if not children:
                return ReadResult(
                    title="Reddit",
                    content=f"⚠️ 帖子不存在或已被删除: {url}",
                    url=url,
                    platform="reddit",
                )

            post = children[0].get("data", {})
            title = post.get("title", "")
            author = post.get("author", "")
            selftext = post.get("selftext", "")
            score = post.get("score", 0)
            subreddit = post.get("subreddit", "")

            # Fix #3: Extract created_utc timestamp
            created = post.get("created_utc", 0)
            date_str = (
                datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                if created
                else ""
            )

            # Extract comments
            comments_text = ""
            if len(data) >= 2:
                comments_text = self._extract_comments(data[1])

            content = selftext
            if comments_text:
                content += f"\n\n---\n## Comments\n{comments_text}"

            return ReadResult(
                title=title,
                content=content,
                url=url,
                author=f"u/{author}",
                platform="reddit",
                date=date_str,
                extra={"subreddit": subreddit, "score": score},
            )

        return ReadResult(
            title="Reddit",
            content=f"⚠️ Reddit 返回了意外格式: {url}",
            url=url,
            platform="reddit",
        )

    def _parse_listing(self, data: dict, url: str) -> ReadResult:
        """Parse a subreddit listing (hot/new/top/rising)."""
        children = data.get("data", {}).get("children", [])

        # Extract subreddit name and sort from URL
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        subreddit = path_parts[1] if len(path_parts) >= 2 else "reddit"
        sort_type = path_parts[2] if len(path_parts) >= 3 else "hot"

        lines = []
        for i, child in enumerate(children, 1):
            if child.get("kind") != "t3":
                continue
            post = child.get("data", {})
            title = post.get("title", "")
            author = post.get("author", "")
            score = post.get("score", 0)
            num_comments = post.get("num_comments", 0)
            permalink = post.get("permalink", "")
            post_url = post.get("url", "")
            is_self = post.get("is_self", False)

            # Fix #3: timestamp in listing items
            created = post.get("created_utc", 0)
            date_str = (
                datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                if created
                else ""
            )

            lines.append(f"### {i}. {title}")
            date_part = f" · 📅 {date_str}" if date_str else ""
            lines.append(f"👤 u/{author} · ⬆ {score} · 💬 {num_comments}{date_part}")
            if not is_self and post_url:
                lines.append(f"🔗 {post_url}")
            lines.append(f"📎 https://www.reddit.com{permalink}")
            # Add selftext preview (first 200 chars)
            selftext = post.get("selftext", "")
            if selftext:
                preview = selftext[:200].replace("\n", " ")
                if len(selftext) > 200:
                    preview += "..."
                lines.append(f"> {preview}")
            lines.append("")

        content = "\n".join(lines) if lines else "No posts found."
        return ReadResult(
            title=f"r/{subreddit} — {sort_type}",
            content=content,
            url=url,
            platform="reddit",
            extra={"subreddit": subreddit, "sort": sort_type, "count": len(children)},
        )

    def _extract_comments(self, comments_data: dict, depth: int = 0, max_depth: int = 3) -> str:
        """Recursively extract comments."""
        lines = []
        children = comments_data.get("data", {}).get("children", [])

        for child in children:
            kind = child.get("kind")

            # Fix #6: Show "more" comments hint instead of silently skipping
            if kind == "more":
                count = child.get("data", {}).get("count", 0)
                if count > 0:
                    indent = "  " * depth
                    lines.append(f"{indent}*[还有 {count} 条评论未加载]*")
                    lines.append("")
                continue

            if kind != "t1":
                continue

            data = child.get("data", {})
            author = data.get("author", "[deleted]")
            body = data.get("body", "")
            score = data.get("score", 0)
            indent = "  " * depth

            lines.append(f"{indent}**u/{author}** ({score} points):")
            lines.append(f"{indent}{body}")
            lines.append("")

            # Recurse into replies
            if depth < max_depth and data.get("replies") and isinstance(data["replies"], dict):
                lines.append(self._extract_comments(data["replies"], depth + 1, max_depth))

        return "\n".join(lines)
