# -*- coding: utf-8 -*-
"""Environment health checker for Agent Eyes.

Checks all platforms, tools, and API keys.
Outputs a rich-formatted status report.
"""

import shutil
import subprocess
from typing import Dict

from agent_eyes.config import Config


STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_OFF = "off"
STATUS_ERROR = "error"


def _check_command(cmd: str) -> bool:
    """Check if a command exists on PATH."""
    return shutil.which(cmd) is not None


def _check_python_import(module: str) -> bool:
    """Check if a Python module is importable."""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def check_all(config: Config) -> Dict[str, dict]:
    """Check all features and return status dict."""
    results = {}

    # === Zero-config (always available) ===
    results["web"] = {
        "status": STATUS_OK,
        "name": "Web Pages",
        "message": "Jina Reader (built-in)",
        "tier": 0,
    }
    results["github_read"] = {
        "status": STATUS_OK,
        "name": "GitHub",
        "message": "Public API (built-in)",
        "tier": 0,
    }
    results["bilibili"] = {
        "status": STATUS_OK,
        "name": "Bilibili",
        "message": "Public API (built-in)",
        "tier": 0,
    }
    results["rss"] = {
        "status": STATUS_OK,
        "name": "RSS",
        "message": "feedparser (built-in)",
        "tier": 0,
    }
    results["tweet_read"] = {
        "status": STATUS_OK,
        "name": "Tweet (single)",
        "message": "Jina Reader (built-in)",
        "tier": 0,
    }

    # YouTube — needs yt-dlp
    if _check_command("yt-dlp"):
        results["youtube"] = {
            "status": STATUS_OK,
            "name": "YouTube",
            "message": "yt-dlp found",
            "tier": 0,
        }
    else:
        results["youtube"] = {
            "status": STATUS_WARN,
            "name": "YouTube",
            "message": "Install yt-dlp: pip install yt-dlp",
            "tier": 0,
        }

    # === Needs API key (Tier 1) ===
    exa_key = config.get("exa_api_key")
    if exa_key:
        results["search_web"] = {
            "status": STATUS_OK,
            "name": "Web Search",
            "message": "Exa API configured",
            "tier": 1,
        }
        results["search_reddit"] = {
            "status": STATUS_OK,
            "name": "Reddit Search",
            "message": "Via Exa (site:reddit.com)",
            "tier": 1,
        }
        results["search_twitter"] = {
            "status": STATUS_OK,
            "name": "Twitter Search",
            "message": "Via Exa (site:x.com)",
            "tier": 1,
        }
    else:
        for key in ("search_web", "search_reddit", "search_twitter"):
            results[key] = {
                "status": STATUS_OFF,
                "name": {"search_web": "Web Search", "search_reddit": "Reddit Search",
                         "search_twitter": "Twitter Search"}[key],
                "message": "Need Exa API key (free). Run: agent-eyes setup",
                "tier": 1,
            }

    # GitHub search (always works, token optional for higher limits)
    github_token = config.get("github_token")
    results["search_github"] = {
        "status": STATUS_OK,
        "name": "GitHub Search",
        "message": f"API ({'authenticated' if github_token else 'public, 60 req/hr'})",
        "tier": 0,
    }

    # === Optional tools (Tier 2) ===

    # Twitter advanced (birdx)
    if _check_command("birdx"):
        results["twitter_advanced"] = {
            "status": STATUS_OK,
            "name": "Twitter Advanced",
            "message": "birdx found",
            "tier": 2,
        }
    else:
        results["twitter_advanced"] = {
            "status": STATUS_OFF,
            "name": "Twitter Advanced",
            "message": "Install birdx for timeline/deep search",
            "tier": 2,
        }

    # Reddit full reader
    reddit_proxy = config.get("reddit_proxy")
    if reddit_proxy:
        results["reddit_full"] = {
            "status": STATUS_OK,
            "name": "Reddit Reader",
            "message": "Proxy configured",
            "tier": 2,
        }
    else:
        results["reddit_full"] = {
            "status": STATUS_OFF,
            "name": "Reddit Reader",
            "message": "Need proxy for full post reading",
            "tier": 2,
        }

    # WeChat / XHS (playwright)
    if _check_python_import("playwright"):
        results["wechat"] = {
            "status": STATUS_OK,
            "name": "WeChat",
            "message": "Playwright available",
            "tier": 2,
        }
        results["xhs"] = {
            "status": STATUS_OK,
            "name": "XiaoHongShu",
            "message": "Playwright available",
            "tier": 2,
        }
    else:
        for key in ("wechat", "xhs"):
            results[key] = {
                "status": STATUS_OFF,
                "name": "WeChat" if key == "wechat" else "XiaoHongShu",
                "message": "pip install agent-eyes[browser]",
                "tier": 2,
            }

    return results


def format_report(results: Dict[str, dict]) -> str:
    """Format results as a readable text report."""
    lines = []
    lines.append("👁️  Agent Eyes Status")
    lines.append("=" * 40)

    # Count stats
    ok_count = sum(1 for r in results.values() if r["status"] == STATUS_OK)
    total = len(results)

    # Group by tier
    lines.append("")
    lines.append("✅ Ready (no setup needed):")
    for key, r in results.items():
        if r["tier"] == 0 and r["status"] == STATUS_OK:
            lines.append(f"  ✅ {r['name']}")
        elif r["tier"] == 0 and r["status"] == STATUS_WARN:
            lines.append(f"  ⚠️  {r['name']} — {r['message']}")

    lines.append("")
    lines.append("🔍 Search (need free Exa API key):")
    for key, r in results.items():
        if r["tier"] == 1:
            icon = "✅" if r["status"] == STATUS_OK else "⬜"
            lines.append(f"  {icon} {r['name']}")

    lines.append("")
    lines.append("🔧 Optional (advanced setup):")
    for key, r in results.items():
        if r["tier"] == 2:
            icon = "✅" if r["status"] == STATUS_OK else "⬜"
            lines.append(f"  {icon} {r['name']} — {r['message']}")

    lines.append("")
    lines.append(f"Status: {ok_count}/{total} platforms active")
    if ok_count < total:
        lines.append("Run `agent-eyes setup` to unlock more!")

    return "\n".join(lines)
