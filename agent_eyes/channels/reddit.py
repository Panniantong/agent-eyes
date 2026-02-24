# -*- coding: utf-8 -*-
"""Reddit — via Reddit JSON API + optional proxy.

Backend: Reddit public JSON API (append .json to any URL)
Swap to: any Reddit access method
"""

import requests
from urllib.parse import urlparse
from .base import Channel, ReadResult


class RedditChannel(Channel):
    name = "reddit"
    description = "Reddit posts and comments"
    backends = ["Reddit JSON API"]
    requires_config = ["reddit_proxy"]
    tier = 2

    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "reddit.com" in domain or "redd.it" in domain

    async def read(self, url: str, config=None) -> ReadResult:
        proxy = config.get("reddit_proxy") if config else None
        proxies = {"http": proxy, "https": proxy} if proxy else None

        # Clean URL: remove query params, trailing slash, then add .json
        parsed = urlparse(url)
        clean_path = parsed.path.rstrip("/")
        # Remove trailing .json if already present (avoid double .json)
        if clean_path.endswith(".json"):
            clean_path = clean_path[:-5]
        json_url = f"https://www.reddit.com{clean_path}.json"

        try:
            resp = requests.get(
                json_url,
                headers={"User-Agent": self.USER_AGENT},
                proxies=proxies,
                params={"limit": 50},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status in (403, 429):
                return ReadResult(
                    title="Reddit",
                    content="⚠️ Reddit blocked this request (403 Forbidden). "
                            "Reddit blocks most server IPs.\n"
                            "Fix: agent-eyes configure proxy http://user:pass@ip:port\n"
                            "Cheap option: https://www.webshare.io ($1/month)\n\n"
                            "Alternatively, search Reddit via Exa (free, no proxy needed): "
                            "agent-eyes search-reddit \"your query\"",
                    url=url,
                    platform="reddit",
                )
            raise

        data = resp.json()

        if isinstance(data, list) and len(data) >= 1:
            # Post page: [post_listing, comments_listing]
            post = data[0]["data"]["children"][0]["data"]
            title = post.get("title", "")
            author = post.get("author", "")
            selftext = post.get("selftext", "")
            score = post.get("score", 0)
            subreddit = post.get("subreddit", "")

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
                extra={"subreddit": subreddit, "score": score},
            )

        raise ValueError(f"Could not parse Reddit response for: {url}")

    def _extract_comments(self, comments_data: dict, depth: int = 0, max_depth: int = 3) -> str:
        """Recursively extract comments."""
        lines = []
        children = comments_data.get("data", {}).get("children", [])

        for child in children:
            if child.get("kind") != "t1":
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
