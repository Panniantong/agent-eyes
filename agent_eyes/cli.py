# -*- coding: utf-8 -*-
"""
Agent Eyes CLI — command-line interface.

Usage:
    agent-eyes read <url>
    agent-eyes search <query>
    agent-eyes search-reddit <query> [--sub <subreddit>]
    agent-eyes search-github <query> [--lang <language>]
    agent-eyes search-twitter <query>
    agent-eyes setup
    agent-eyes doctor
    agent-eyes version
"""

import sys
import asyncio
import argparse
import json

from agent_eyes import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="agent-eyes",
        description="👁️ Give your AI Agent eyes to see the entire internet",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── read ──
    p_read = sub.add_parser("read", help="Read content from a URL")
    p_read.add_argument("url", help="URL to read")
    p_read.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")

    # ── search ──
    p_search = sub.add_parser("search", help="Search the web (Exa)")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("-n", "--num", type=int, default=5, help="Number of results")

    # ── search-reddit ──
    p_sr = sub.add_parser("search-reddit", help="Search Reddit")
    p_sr.add_argument("query", nargs="+", help="Search query")
    p_sr.add_argument("--sub", help="Subreddit filter")
    p_sr.add_argument("-n", "--num", type=int, default=10, help="Number of results")

    # ── search-github ──
    p_sg = sub.add_parser("search-github", help="Search GitHub")
    p_sg.add_argument("query", nargs="+", help="Search query")
    p_sg.add_argument("--lang", help="Language filter")
    p_sg.add_argument("-n", "--num", type=int, default=5, help="Number of results")

    # ── search-twitter ──
    p_st = sub.add_parser("search-twitter", help="Search Twitter")
    p_st.add_argument("query", nargs="+", help="Search query")
    p_st.add_argument("-n", "--num", type=int, default=10, help="Number of results")

    # ── setup ──
    sub.add_parser("setup", help="Interactive configuration wizard")

    # ── doctor ──
    sub.add_parser("doctor", help="Check platform availability")

    # ── version ──
    sub.add_parser("version", help="Show version")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "version":
        print(f"Agent Eyes v{__version__}")
        sys.exit(0)

    if args.command == "doctor":
        _cmd_doctor()
    elif args.command == "setup":
        _cmd_setup()
    elif args.command == "read":
        asyncio.run(_cmd_read(args))
    elif args.command.startswith("search"):
        asyncio.run(_cmd_search(args))


# ── Command handlers ────────────────────────────────


def _cmd_doctor():
    from agent_eyes.config import Config
    from agent_eyes.doctor import check_all, format_report
    config = Config()
    results = check_all(config)
    print(format_report(results))


def _cmd_setup():
    from agent_eyes.config import Config

    config = Config()
    print()
    print("👁️  Agent Eyes Setup")
    print("=" * 40)
    print()

    # Step 1: Exa
    print("【推荐】全网搜索 — Exa Search API")
    print("  免费 1000 次/月，注册地址: https://exa.ai")
    current = config.get("exa_api_key")
    if current:
        print(f"  当前状态: ✅ 已配置 ({current[:8]}...)")
        change = input("  要更换吗？[y/N]: ").strip().lower()
        if change != "y":
            print()
        else:
            key = input("  EXA_API_KEY: ").strip()
            if key:
                config.set("exa_api_key", key)
                print("  ✅ 已更新！")
            print()
    else:
        print("  当前状态: ⬜ 未配置")
        key = input("  EXA_API_KEY (回车跳过): ").strip()
        if key:
            config.set("exa_api_key", key)
            print("  ✅ 全网搜索 + Reddit搜索 + Twitter搜索 已开启！")
        else:
            print("  ℹ️  跳过。稍后可运行 agent-eyes setup 配置")
        print()

    # Step 2: GitHub token
    print("【可选】GitHub Token — 提高 API 限额")
    print("  无 token: 60 次/小时 | 有 token: 5000 次/小时")
    print("  获取: https://github.com/settings/tokens (无需任何权限)")
    current = config.get("github_token")
    if current:
        print(f"  当前状态: ✅ 已配置")
    else:
        key = input("  GITHUB_TOKEN (回车跳过): ").strip()
        if key:
            config.set("github_token", key)
            print("  ✅ GitHub API 已提升至 5000 次/小时！")
        else:
            print("  ℹ️  跳过。公开 API 也能用")
    print()

    # Step 3: Reddit proxy
    print("【可选】Reddit 代理 — 完整阅读 Reddit 帖子+评论")
    print("  Reddit 封锁很多 IP，需要 ISP 代理才能直接访问")
    print("  格式: http://用户名:密码@IP:端口")
    current = config.get("reddit_proxy")
    if current:
        print(f"  当前状态: ✅ 已配置")
    else:
        proxy = input("  REDDIT_PROXY (回车跳过): ").strip()
        if proxy:
            config.set("reddit_proxy", proxy)
            print("  ✅ Reddit 完整阅读已开启！")
        else:
            print("  ℹ️  跳过。仍可通过搜索获取 Reddit 内容")
    print()

    # Step 4: Groq (Whisper)
    print("【可选】Groq API — 视频无字幕时的语音转文字")
    print("  免费额度，注册: https://console.groq.com")
    current = config.get("groq_api_key")
    if current:
        print(f"  当前状态: ✅ 已配置")
    else:
        key = input("  GROQ_API_KEY (回车跳过): ").strip()
        if key:
            config.set("groq_api_key", key)
            print("  ✅ 语音转文字已开启！")
        else:
            print("  ℹ️  跳过")
    print()

    # Summary
    print("=" * 40)
    print(f"✅ 配置已保存到 {config.config_path}")
    print("运行 agent-eyes doctor 查看完整状态")
    print()


async def _cmd_read(args):
    from agent_eyes.core import AgentEyes
    eyes = AgentEyes()
    try:
        result = await eyes.read(args.url)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n📖 {result.get('title', 'Untitled')}")
            print(f"🔗 {result.get('url', '')}")
            if result.get("author"):
                print(f"👤 {result['author']}")
            print(f"\n{result.get('content', '')}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


async def _cmd_search(args):
    from agent_eyes.core import AgentEyes
    eyes = AgentEyes()
    query = " ".join(args.query)
    num = args.num

    try:
        if args.command == "search":
            results = await eyes.search(query, num_results=num)
        elif args.command == "search-reddit":
            results = await eyes.search_reddit(query, subreddit=getattr(args, "sub", None), limit=num)
        elif args.command == "search-github":
            results = await eyes.search_github(query, language=getattr(args, "lang", None), limit=num)
        elif args.command == "search-twitter":
            results = await eyes.search_twitter(query, limit=num)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        if not results:
            print("No results found.")
            return

        for i, r in enumerate(results, 1):
            title = r.get("title") or r.get("name") or r.get("text", "")[:60]
            url = r.get("url", "")
            snippet = r.get("snippet") or r.get("description") or r.get("text", "")
            print(f"\n{i}. {title}")
            print(f"   🔗 {url}")
            if snippet:
                print(f"   {snippet[:200]}")
            # Extra info for GitHub
            if "stars" in r:
                print(f"   ⭐ {r['stars']}  🍴 {r.get('forks', 0)}  📝 {r.get('language', '')}")

    except ValueError as e:
        print(f"⚠️  {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
