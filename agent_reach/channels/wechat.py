# -*- coding: utf-8 -*-
"""WeChat Official Account articles — read and search.

Read:   wechat-article-for-ai (Camoufox stealth browser)
Search: miku_ai (Sogou WeChat search)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .base import Channel


class WeChatChannel(Channel):
    name = "wechat"
    description = "微信公众号文章"
    backends = ["wechat-article-for-ai (Camoufox)", "miku_ai (搜狗搜索)"]
    tier = 2

    # Default tool directory
    _TOOL_DIR = os.path.expanduser("~/.agent-reach/tools/wechat-article-for-ai")

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        return "mp.weixin.qq.com" in d or "weixin.qq.com" in d

    def read(self, url: str, output_dir: str = "/tmp/wechat-articles",
             no_images: bool = False) -> dict:
        """Read a WeChat article and return structured metadata + content.

        Returns a dict with: title, author, date, url, output_path, content,
        char_count, image_count, success, error.

        This wraps wechat-article-for-ai and captures both its structured
        output AND parses the generated markdown, so callers always get
        the title and content — not just log messages.
        """
        result = {
            "success": False,
            "title": "",
            "author": "",
            "date": "",
            "url": url,
            "output_path": "",
            "content": "",
            "char_count": 0,
            "image_count": 0,
            "error": "",
        }

        tool_dir = Path(self._TOOL_DIR)
        if not (tool_dir / "main.py").exists():
            result["error"] = (
                f"wechat-article-for-ai not found at {tool_dir}. "
                "Run: agent-reach install"
            )
            return result

        # Build command
        cmd = [sys.executable, "main.py", url, "-o", output_dir]
        if no_images:
            cmd.append("--no-images")

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(tool_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            result["error"] = "Timed out after 120 seconds"
            return result
        except Exception as e:
            result["error"] = f"Failed to run tool: {e}"
            return result

        # Parse title/author from log output (stderr)
        for line in proc.stderr.splitlines():
            line_stripped = line.strip()
            # Logger lines look like: "INFO ... Title: xxx"
            if "Title:" in line_stripped:
                result["title"] = line_stripped.split("Title:", 1)[1].strip()
            elif "Author:" in line_stripped:
                result["author"] = line_stripped.split("Author:", 1)[1].strip()
            elif "Saved:" in line_stripped:
                saved_part = line_stripped.split("Saved:", 1)[1].strip()
                # Extract path (before the parenthetical stats)
                if " (" in saved_part:
                    saved_part = saved_part.split(" (")[0].strip()
                result["output_path"] = saved_part

        # If we got an output path, read the generated markdown for content
        if result["output_path"]:
            md_path = Path(result["output_path"])
            if md_path.exists():
                content = md_path.read_text(encoding="utf-8")
                result["content"] = content
                result["char_count"] = len(content)

                # Extract title from frontmatter if not found in logs
                if not result["title"] and content.startswith("---"):
                    for fm_line in content.split("---", 2)[1].splitlines():
                        if fm_line.strip().startswith("title:"):
                            result["title"] = fm_line.split("title:", 1)[1].strip().strip('"').strip("'")
                            break

        # Also try to find the output directory by scanning output_dir
        if not result["output_path"]:
            out = Path(output_dir)
            if out.exists():
                # Find the most recently created .md file
                md_files = sorted(out.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
                if md_files:
                    md_path = md_files[0]
                    result["output_path"] = str(md_path)
                    content = md_path.read_text(encoding="utf-8")
                    result["content"] = content
                    result["char_count"] = len(content)

                    if not result["title"]:
                        # Use directory name as fallback title
                        result["title"] = md_path.parent.name

        result["success"] = proc.returncode == 0 and bool(result["title"])

        if proc.returncode != 0 and not result["error"]:
            result["error"] = proc.stderr.strip()[-500:] if proc.stderr else "Unknown error"

        return result

    def check(self, config=None):
        has_read = False
        has_search = False

        try:
            import camoufox  # noqa: F401
            has_read = True
        except ImportError:
            pass

        try:
            import miku_ai  # noqa: F401
            has_search = True
        except ImportError:
            pass

        if has_read and has_search:
            return "ok", "完整可用（搜索 + 阅读公众号文章）"
        elif has_read:
            return "ok", "可阅读公众号文章（URL → Markdown）。安装 miku_ai 可解锁搜索：pip install miku_ai"
        elif has_search:
            return "warn", (
                "可搜索公众号文章但无法阅读全文。安装阅读工具：\n"
                "  pip install camoufox[geoip] markdownify beautifulsoup4 httpx mcp"
            )
        else:
            return "off", (
                "需要安装微信公众号工具：\n"
                "  # 阅读（URL → Markdown）：\n"
                "  pip install camoufox[geoip] markdownify beautifulsoup4 httpx mcp\n"
                "  # 搜索（关键词 → 文章列表）：\n"
                "  pip install miku_ai\n"
                "  详见 https://github.com/bzd6661/wechat-article-for-ai"
            )
