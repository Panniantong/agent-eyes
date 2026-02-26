# -*- coding: utf-8 -*-
"""Instagram — via instaloader (free, open source).

Backend: instaloader (9.8K stars, Python CLI + library)
Swap to: any Instagram access tool

Known limitations (as of 2026-02):
  Instagram has increasingly aggressive anti-bot measures. Even with valid
  cookies/sessions, instaloader may return 401 or "Something went wrong".
  See: https://github.com/instaloader/instaloader/issues/2585
       https://github.com/instaloader/instaloader/issues/2648
  When instaloader fails, we fall back to Jina Reader for public content.
"""

import logging
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List

logger = logging.getLogger(__name__)


class InstagramChannel(Channel):
    name = "instagram"
    description = "Instagram 帖子和 Profile"
    backends = ["instaloader"]
    tier = 2  # Needs login for full access

    def can_handle(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return "instagram.com" in domain or "instagr.am" in domain

    def check(self, config=None):
        # Check both CLI and Python module
        has_cli = shutil.which("instaloader")
        has_module = False
        try:
            import instaloader
            has_module = True
        except ImportError:
            pass

        if not has_cli and not has_module:
            return "off", (
                "需要安装 instaloader：pip install instaloader\n"
                "  安装后可读取 Instagram 帖子和 Profile\n"
                "  登录: agent-reach configure instagram-cookies \"sessionid=xxx; csrftoken=yyy; ...\""
            )

        # Check if cookies are configured
        cookie_file = Path.home() / ".agent-reach" / "instagram-cookies.txt"
        session_ok = self._check_session_file(cookie_file)

        if cookie_file.exists():
            if session_ok:
                return "ok", (
                    "已配置 cookies，可读取 Instagram 帖子和 Profile\n"
                    "  ⚠️ 注意：Instagram 反爬较严，如遇 401/\"Something went wrong\"，\n"
                    "  请尝试用 instaloader --login USERNAME 方式登录"
                )
            else:
                return "warn", (
                    "cookies 文件存在但格式可能有问题（缺少 sessionid 或 csrftoken）\n"
                    '  重新配置: agent-reach configure instagram-cookies "sessionid=xxx; csrftoken=yyy; ..."'
                )
        return "ok", (
            "可读取公开帖子和 Profile。登录可访问更多内容：\n"
            '  agent-reach configure instagram-cookies "sessionid=xxx; csrftoken=yyy; ..."\n'
            "  或: agent-reach configure --from-browser chrome（自动提取）"
        )

    def _check_session_file(self, cookie_file: Path) -> bool:
        """Validate cookie file has required fields."""
        if not cookie_file.exists():
            return False
        try:
            cookie_str = cookie_file.read_text().strip()
            cookies = self._parse_cookies(cookie_str)
            return "sessionid" in cookies and "csrftoken" in cookies
        except Exception:
            return False

    @staticmethod
    def _parse_cookies(cookie_str: str) -> dict:
        """Parse cookie header string into dict."""
        cookies = {}
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies

    async def read(self, url: str, config=None) -> ReadResult:
        # Try instaloader (module or CLI)
        try:
            import instaloader
            return await self._read_instaloader(url, config)
        except ImportError:
            pass
        # Fallback: Jina Reader
        return await self._read_jina(url)

    async def _read_instaloader(self, url: str, config=None) -> ReadResult:
        """Read Instagram content using instaloader Python API."""
        import asyncio
        import concurrent.futures

        instaloader_error = None

        def _sync_read():
            nonlocal instaloader_error
            import instaloader
            L = instaloader.Instaloader(
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                max_connection_attempts=1,  # Don't retry on rate limit
            )

            # Try to load session: cookie file > saved session
            session_loaded = False
            cookie_file = Path.home() / ".agent-reach" / "instagram-cookies.txt"
            if cookie_file.exists():
                try:
                    cookie_str = cookie_file.read_text().strip()
                    cookies = self._parse_cookies(cookie_str)
                    if "sessionid" in cookies and "csrftoken" in cookies:
                        # ds_user_id is numeric; instaloader stores username
                        # for session management but it doesn't affect API calls
                        username = cookies.get("ds_user_id", "user")
                        L.context.load_session(username, cookies)
                        session_loaded = True
                        logger.debug("Instagram session loaded from cookie file")
                except Exception as e:
                    logger.warning("Failed to load Instagram cookies: %s", e)

            if not session_loaded and config and config.get("instagram_username"):
                try:
                    L.load_session_from_file(config.get("instagram_username"))
                    session_loaded = True
                    logger.debug("Instagram session loaded from session file")
                except Exception as e:
                    logger.warning("Failed to load Instagram session file: %s", e)

            path = urlparse(url).path.strip("/")

            if "/p/" in url or "/reel/" in url:
                return self._read_post_sync(L, url, path)
            else:
                return self._read_profile_sync(L, url, path)

        try:
            # Run with 15s timeout to avoid instaloader's 30-min retry
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await asyncio.wait_for(
                    loop.run_in_executor(pool, _sync_read),
                    timeout=15,
                )
                return result
        except asyncio.TimeoutError:
            logger.warning("Instaloader timed out for %s, falling back to Jina", url)
            return await self._read_jina(url, hint="instaloader 请求超时")
        except Exception as e:
            error_msg = str(e)
            logger.warning("Instaloader failed for %s: %s", url, error_msg)

            # Provide specific hints based on error type
            hint = "instaloader 出错"
            if "401" in error_msg or "Unauthorized" in error_msg:
                hint = (
                    "Instagram 返回 401 Unauthorized。这是 Instagram 反爬机制导致的已知问题。\n"
                    "建议：1) 用 instaloader --login USERNAME 交互式登录\n"
                    "      2) 或在浏览器中重新获取 cookies"
                )
            elif "redirected to login" in error_msg.lower() or "login" in error_msg.lower():
                hint = (
                    "被重定向到登录页面。cookies 可能已过期或被 Instagram 标记。\n"
                    "建议：在浏览器中重新登录 Instagram，然后重新配置 cookies"
                )
            elif "something went wrong" in error_msg.lower():
                hint = (
                    "Instagram 返回 \"Something went wrong\"。这是 Instagram 的通用反爬响应。\n"
                    "参考: https://github.com/instaloader/instaloader/issues/2648"
                )
            elif "rate" in error_msg.lower() or "wait" in error_msg.lower():
                hint = "Instagram 速率限制，请稍后再试"

            return await self._read_jina(url, hint=hint)

    def _read_post_sync(self, L, url: str, path: str) -> ReadResult:
        """Read a single Instagram post (sync, runs in executor)."""
        import instaloader

        # Extract shortcode from URL
        match = re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)", url)
        if not match:
            raise ValueError("Cannot extract shortcode from URL")

        shortcode = match.group(1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        lines = []
        if post.caption:
            lines.append(post.caption)
        lines.append("")
        lines.append(f"👤 @{post.owner_username}")
        lines.append(f"❤️ {post.likes} likes")
        if post.comments:
            lines.append(f"💬 {post.comments} comments")
        lines.append(f"📅 {post.date_utc.strftime('%Y-%m-%d %H:%M')}")
        if post.location:
            lines.append(f"📍 {post.location}")
        if post.hashtags:
            lines.append(f"#️⃣ {' '.join('#' + h for h in post.hashtags)}")

        return ReadResult(
            title=f"@{post.owner_username}: {(post.caption or '')[:80]}",
            content="\n".join(lines),
            url=url,
            author=f"@{post.owner_username}",
            date=post.date_utc.strftime("%Y-%m-%d"),
            platform="instagram",
            extra={"likes": post.likes, "comments": post.comments},
        )

    def _read_profile_sync(self, L, url: str, path: str) -> ReadResult:
        """Read an Instagram profile (sync, runs in executor)."""
        import instaloader

        # Extract username from path
        username = path.split("/")[0] if path else ""
        if not username or username in ("p", "reel", "stories", "explore"):
            raise ValueError("Cannot extract username from URL")

        profile = instaloader.Profile.from_username(L.context, username)

        lines = []
        lines.append(f"👤 {profile.full_name} (@{profile.username})")
        if profile.biography:
            lines.append(f"📝 {profile.biography}")
        if profile.external_url:
            lines.append(f"🔗 {profile.external_url}")
        lines.append("")
        lines.append(f"📊 {profile.mediacount} posts · "
                     f"{profile.followers} followers · "
                     f"{profile.followees} following")
        if profile.is_verified:
            lines.append("✅ Verified")
        if profile.is_business_account and profile.business_category_name:
            lines.append(f"🏢 {profile.business_category_name}")

        # Get recent posts (up to 5)
        lines.append("")
        lines.append("📸 Recent posts:")
        count = 0
        try:
            for post in profile.get_posts():
                if count >= 5:
                    break
                caption = (post.caption or "")[:100].replace("\n", " ")
                lines.append(f"  • ❤️{post.likes} | {post.date_utc.strftime('%m-%d')} | {caption}")
                count += 1
        except Exception as e:
            # Posts listing may fail even if profile loads fine
            logger.debug("Failed to list posts for %s: %s", username, e)
            if count == 0:
                lines.append("  （获取帖子列表失败，可能是 Instagram 限制）")

        return ReadResult(
            title=f"{profile.full_name} (@{profile.username}) - Instagram",
            content="\n".join(lines),
            url=url,
            author=f"@{profile.username}",
            platform="instagram",
            extra={
                "followers": profile.followers,
                "posts": profile.mediacount,
            },
        )

    async def _read_jina(self, url: str, hint: str = "") -> ReadResult:
        """Fallback: use Jina Reader."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://r.jina.ai/{url}",
                    headers={"Accept": "text/markdown"},
                )
                resp.raise_for_status()
            text = resp.text

            # Prepend hint if instaloader failed with a specific reason
            if hint:
                text = f"⚠️ {hint}\n（以下为 Jina Reader 抓取的公开内容）\n\n{text}"

            return ReadResult(
                title=text[:100] if text else url,
                content=text,
                url=url,
                platform="instagram",
            )
        except Exception:
            content_parts = [f"⚠️ 无法读取此 Instagram 内容: {url}"]
            if hint:
                content_parts.append(f"\n原因: {hint}")
            content_parts.append(
                "\n\n提示：\n"
                "- 确保 URL 正确\n"
                "- 安装 instaloader: pip install instaloader\n"
                "- 登录方式 1: instaloader --login YOUR_USERNAME（推荐，交互式登录）\n"
                '- 登录方式 2: agent-reach configure instagram-cookies "sessionid=xxx; csrftoken=yyy; ..."\n'
                "- 登录方式 3: agent-reach configure --from-browser chrome（自动从浏览器提取）\n"
                "\n"
                "⚠️ 注意：Instagram 反爬机制较严，即使配置了 cookies 也可能无法访问。\n"
                "这是 instaloader 上游的已知问题: https://github.com/instaloader/instaloader/issues/2585"
            )
            return ReadResult(
                title="Instagram",
                content="".join(content_parts),
                url=url,
                platform="instagram",
            )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        """Search Instagram via Exa."""
        limit = kwargs.get("limit", 10)
        from agent_reach.channels.exa_search import ExaSearchChannel
        exa = ExaSearchChannel()
        return await exa.search(f"site:instagram.com {query}", config=config, limit=limit)
