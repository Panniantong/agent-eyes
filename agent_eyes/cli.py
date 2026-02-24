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
import os

from agent_eyes import __version__


def _configure_logging(verbose: bool = False):
    """Suppress loguru output unless --verbose is set."""
    from loguru import logger
    logger.remove()  # Remove default stderr handler
    if verbose:
        logger.add(sys.stderr, level="INFO")


def main():
    parser = argparse.ArgumentParser(
        prog="agent-eyes",
        description="👁️ Give your AI Agent eyes to see the entire internet",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug logs")
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

    # ── install ──
    p_install = sub.add_parser("install", help="One-shot installer with flags")
    p_install.add_argument("--env", choices=["local", "server", "auto"], default="auto",
                           help="Environment: local, server, or auto-detect")
    p_install.add_argument("--search", choices=["yes", "no"], default="yes",
                           help="Enable web search (needs free Exa API key)")
    p_install.add_argument("--proxy", default="",
                           help="Residential proxy for Reddit/Bilibili (http://user:pass@ip:port)")
    p_install.add_argument("--exa-key", default="",
                           help="Exa API key (get free at https://exa.ai)")

    # ── configure ──
    p_conf = sub.add_parser("configure", help="Set a config value or auto-extract from browser")
    p_conf.add_argument("key", nargs="?", default=None,
                        choices=["exa-key", "proxy", "github-token", "groq-key",
                                 "twitter-cookies", "xhs-cookie", "youtube-cookies"],
                        help="What to configure (omit if using --from-browser)")
    p_conf.add_argument("value", nargs="*", help="The value(s) to set")
    p_conf.add_argument("--from-browser", metavar="BROWSER",
                        choices=["chrome", "firefox", "edge", "brave", "opera"],
                        help="Auto-extract ALL platform cookies from browser (chrome/firefox/edge/brave/opera)")

    # ── doctor ──
    sub.add_parser("doctor", help="Check platform availability")

    # ── version ──
    sub.add_parser("version", help="Show version")

    args = parser.parse_args()

    # Suppress loguru noise unless --verbose
    _configure_logging(getattr(args, "verbose", False))

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
    elif args.command == "install":
        _cmd_install(args)
    elif args.command == "configure":
        _cmd_configure(args)
    elif args.command == "read":
        asyncio.run(_cmd_read(args))
    elif args.command.startswith("search"):
        asyncio.run(_cmd_search(args))


# ── Command handlers ────────────────────────────────


def _cmd_install(args):
    """One-shot deterministic installer."""
    from agent_eyes.config import Config
    from agent_eyes.doctor import check_all, format_report

    config = Config()
    print()
    print("👁️  Agent Eyes Installer")
    print("=" * 40)

    # Auto-detect environment
    env = args.env
    if env == "auto":
        env = _detect_environment()
    
    if env == "server":
        print(f"📡 Environment: Server/VPS (auto-detected)")
    else:
        print(f"💻 Environment: Local computer (auto-detected)")

    # Apply flags
    if args.exa_key:
        config.set("exa_api_key", args.exa_key)
        print(f"✅ Exa search key configured")

    if args.proxy:
        config.set("reddit_proxy", args.proxy)
        config.set("bilibili_proxy", args.proxy)
        print(f"✅ Proxy configured for Reddit + Bilibili")

    # Environment-specific advice
    if env == "server" and not args.proxy:
        print()
        print("💡 Tip: Reddit and Bilibili block server IPs.")
        print("   Reddit search still works via Exa (free).")
        print("   For full access: agent-eyes configure proxy http://user:pass@ip:port")
        print("   Cheap option: https://www.webshare.io ($1/month)")

    # Test channels
    print()
    print("Testing channels...")
    results = check_all(config)
    ok = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)
    print(f"✅ {ok}/{total} channels active")

    # What's missing
    if args.search == "yes" and not args.exa_key and not config.get("exa_api_key"):
        print()
        print("🔍 Recommended: unlock search with a free Exa API key")
        print("   agent-eyes configure exa-key YOUR_KEY")
        print("   Get free key: https://exa.ai")

    # Final status
    print()
    print(format_report(results))
    print()
    print("✅ Installation complete!")


def _detect_environment():
    """Auto-detect if running on local computer or server."""
    import os

    # Check common server indicators
    indicators = 0

    # SSH session
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"):
        indicators += 2

    # Docker / container
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        indicators += 2

    # No display (headless)
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        indicators += 1

    # Cloud VM identifiers
    for cloud_file in ["/sys/hypervisor/uuid", "/sys/class/dmi/id/product_name"]:
        if os.path.exists(cloud_file):
            try:
                content = open(cloud_file).read().lower()
                if any(x in content for x in ["amazon", "google", "microsoft", "digitalocean", "linode", "vultr", "hetzner"]):
                    indicators += 2
            except:
                pass

    # systemd-detect-virt
    try:
        import subprocess
        result = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip() != "none":
            indicators += 1
    except:
        pass

    return "server" if indicators >= 2 else "local"


def _cmd_configure(args):
    """Set a config value and test it, or auto-extract from browser."""
    from agent_eyes.config import Config

    config = Config()

    # ── Auto-extract from browser ──
    if args.from_browser:
        from agent_eyes.cookie_extract import configure_from_browser

        browser = args.from_browser
        print(f"🔍 Extracting cookies from {browser}...")
        print()

        results = configure_from_browser(browser, config)

        found_any = False
        for platform, success, message in results:
            if success:
                print(f"  ✅ {platform}: {message}")
                found_any = True
            else:
                print(f"  ⬜ {platform}: {message}")

        print()
        if found_any:
            print("✅ Cookies configured! Run `agent-eyes doctor` to see updated status.")
        else:
            print(f"No cookies found. Make sure you're logged into the platforms in {browser}.")
        return

    # ── Manual configure ──
    if not args.key:
        print("Usage: agent-eyes configure <key> <value>")
        print("   or: agent-eyes configure --from-browser chrome")
        return

    value = " ".join(args.value) if args.value else ""
    if not value:
        print(f"Missing value for {args.key}")
        return

    if args.key == "proxy":
        config.set("reddit_proxy", value)
        config.set("bilibili_proxy", value)
        print(f"✅ Proxy configured for Reddit + Bilibili!")

        # Auto-test
        print("Testing Reddit access...", end=" ")
        try:
            import requests
            resp = requests.get(
                "https://www.reddit.com/r/test.json?limit=1",
                headers={"User-Agent": "Mozilla/5.0"},
                proxies={"http": value, "https": value},
                timeout=10,
            )
            if resp.status_code == 200:
                print("✅ Reddit works!")
            else:
                print(f"⚠️ Reddit returned {resp.status_code}")
        except Exception as e:
            print(f"❌ Failed: {e}")

    elif args.key == "exa-key":
        config.set("exa_api_key", value)
        print(f"✅ Exa key configured!")

        print("Testing search...", end=" ")
        try:
            import asyncio
            from agent_eyes.core import AgentEyes
            eyes = AgentEyes(config)
            results = asyncio.run(eyes.search("test", num_results=1))
            if results:
                print("✅ Search works!")
            else:
                print("⚠️ No results, but API connected.")
        except Exception as e:
            print(f"❌ Failed: {e}")

    elif args.key == "twitter-cookies":
        # Accept two formats:
        # 1. auth_token ct0 (two separate values)
        # 2. Full cookie header string: "auth_token=xxx; ct0=yyy; ..."
        auth_token = None
        ct0 = None

        if "auth_token=" in value and "ct0=" in value:
            # Full cookie string — parse it
            for part in value.replace(";", " ").split():
                if part.startswith("auth_token="):
                    auth_token = part.split("=", 1)[1]
                elif part.startswith("ct0="):
                    ct0 = part.split("=", 1)[1]
        elif len(value.split()) == 2 and "=" not in value:
            # Two separate values: AUTH_TOKEN CT0
            parts = value.split()
            auth_token = parts[0]
            ct0 = parts[1]

        if auth_token and ct0:
            config.set("twitter_auth_token", auth_token)
            config.set("twitter_ct0", ct0)
            print(f"✅ Twitter cookies configured!")

            print("Testing Twitter access...", end=" ")
            try:
                import subprocess
                result = subprocess.run(
                    ["birdx", "search", "test", "-n", "1",
                     "--auth-token", auth_token, "--ct0", ct0],
                    capture_output=True, text=True, timeout=15,
                )
                if result.returncode == 0 and result.stdout.strip():
                    print("✅ Twitter Advanced works!")
                else:
                    print(f"⚠️ Test returned no results (cookies might be wrong)")
            except FileNotFoundError:
                print("⚠️ birdx not installed. Run: pip install birdx")
            except Exception as e:
                print(f"❌ Failed: {e}")
        else:
            print("❌ Could not find auth_token and ct0 in your input.")
            print("   Accepted formats:")
            print("   1. agent-eyes configure twitter-cookies AUTH_TOKEN CT0")
            print('   2. agent-eyes configure twitter-cookies "auth_token=xxx; ct0=yyy; ..."')

    elif args.key == "xhs-cookie":
        config.set("xhs_cookie", value)
        print(f"✅ XiaoHongShu cookie configured!")

        print("Testing XHS access...", end=" ")
        try:
            import requests
            resp = requests.get(
                "https://www.xiaohongshu.com/",
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Cookie": value,
                },
                timeout=10,
            )
            if resp.status_code == 200 and "xiaohongshu" in resp.text.lower():
                print("✅ XiaoHongShu works!")
            else:
                print(f"⚠️ Got status {resp.status_code}, cookie might be expired")
        except Exception as e:
            print(f"❌ Failed: {e}")

    elif args.key == "youtube-cookies":
        config.set("youtube_cookies_from", value)
        print(f"✅ YouTube cookie source configured: {value}")
        print("   yt-dlp will use cookies from this browser for age-restricted/member videos.")

    elif args.key == "github-token":
        config.set("github_token", value)
        print(f"✅ GitHub token configured!")

    elif args.key == "groq-key":
        config.set("groq_api_key", value)
        print(f"✅ Groq key configured!")


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
