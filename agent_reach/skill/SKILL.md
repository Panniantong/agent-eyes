---
name: agent-reach
description: >
  Give your AI agent eyes to see the entire internet. Read and search across
  Twitter/X, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu, Instagram, LinkedIn,
  Boss直聘, RSS, and any web page — all from a single CLI.
  Use when: (1) reading content from URLs (tweets, Reddit posts, articles, videos),
  (2) searching across platforms (web, Twitter, Reddit, GitHub, YouTube, Bilibili,
  XiaoHongShu, Instagram, LinkedIn, Boss直聘),
  (3) user asks to configure/enable a platform channel,
  (4) checking channel health or updating Agent Reach.
  Triggers: "search Twitter/Reddit/YouTube", "read this URL", "find posts about",
  "搜索", "读取", "查一下", "看看这个链接",
  "帮我配", "帮我添加", "帮我安装".
---

# Agent Reach

Read and search the internet across 12+ platforms via unified CLI.

## Setup

First check if agent-reach is installed:
```bash
agent-reach doctor
```

If command not found, install it:
```bash
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

`install` auto-detects your environment and installs core dependencies (Node.js, mcporter, bird CLI, gh CLI, instaloader). Read the output and run `agent-reach doctor` to see what's active.

## Commands

### Read any URL
```bash
agent-reach read <url>
agent-reach read <url> --json    # structured output
```
Handles: tweets, Reddit posts, articles, YouTube/Bilibili (transcripts), GitHub repos, Instagram posts, LinkedIn profiles, Boss直聘 jobs, XiaoHongShu notes, RSS feeds, and any web page.

### Search

```bash
agent-reach search "query"             # web search (Exa)
agent-reach search-twitter "query"     # Twitter/X
agent-reach search-reddit "query"      # Reddit (--sub <subreddit>)
agent-reach search-github "query"      # GitHub (--lang <language>)
agent-reach search-youtube "query"     # YouTube
agent-reach search-bilibili "query"    # Bilibili (B站)
agent-reach search-xhs "query"        # XiaoHongShu (小红书)
agent-reach search-instagram "query"   # Instagram
agent-reach search-linkedin "query"    # LinkedIn
agent-reach search-bosszhipin "query"  # Boss直聘
```

All search commands support `-n <count>` for number of results.

### Management

```bash
agent-reach doctor        # channel status overview
agent-reach watch         # quick health + update check (for scheduled tasks)
agent-reach check-update  # check for new versions
```

### Configure channels

```bash
agent-reach configure twitter-cookies "auth_token=xxx; ct0=yyy"
agent-reach configure instagram-cookies "sessionid=xxx; csrftoken=yyy; ..."
agent-reach configure proxy http://user:pass@ip:port
agent-reach configure --from-browser chrome    # auto-extract cookies from local browser
```

## Configuring a channel ("帮我配 XXX")

All channels follow the same flow. When a user asks to configure/enable any channel:

1. Run `agent-reach doctor`
2. Find the channel in the output — it shows the current status (✅/⚠️/⬜) and **what to do next**
3. Execute whatever you can automatically (install packages, start services, register MCP)
4. For steps that require human action (scan QR code, paste cookies, login), tell the user exactly what to do
5. After the user completes their part, run `agent-reach doctor` again to verify

**Do NOT memorize per-channel steps.** Always rely on `doctor` output — it stays up-to-date even when backends change.

### Common human actions

These are things only the user can do. When `doctor` indicates one is needed, explain it clearly:

- **Paste cookies:** User installs [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) Chrome extension → goes to the website → exports Header String → sends it to you → you run `agent-reach configure <platform>-cookies "..."`
- **Scan QR code:** User opens the URL shown in `doctor` output on their phone/browser and scans with the platform's app
- **Browser login:** Some MCP services need a one-time browser login; on servers without a display, user may need VNC
- **Proxy:** Reddit/Bilibili/XiaoHongShu block server IPs — suggest a residential proxy (~$1/month) if on a server

## Tips

- Always try `agent-reach read <url>` first for any URL — it auto-detects the platform
- If a channel is ⬜ but the user hasn't asked for it, don't push — let them opt in
- If a channel breaks, run `agent-reach doctor` to diagnose
- LinkedIn and Boss直聘 have Jina Reader fallback even without full setup
