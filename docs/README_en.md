<h1 align="center">👁️ Agent Reach</h1>

<p align="center">
  <strong>Give your AI Agent one-click access to the entire internet</strong>
</p>

<p align="center">
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/Panniantong/agent-reach/stargazers"><img src="https://img.shields.io/github/stars/Panniantong/agent-reach?style=for-the-badge" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#get-started-in-30-seconds">Quick Start</a> · <a href="../README.md">中文</a> · <a href="#supported-platforms">Platforms</a> · <a href="#design-philosophy">Philosophy</a>
</p>

---

## Why Agent Reach?

AI Agents can already access the internet — but "can go online" is barely the start.

The most valuable information lives across social and niche platforms: Twitter discussions, Reddit feedback, XiaoHongShu reviews, Bilibili videos, GitHub activity… **These are where information density is highest**, but each platform has its own barriers:

| Pain Point | Reality |
|------------|---------|
| Twitter API | Starts at $100/month |
| Reddit | Server IPs get 403'd |
| XiaoHongShu | Login required to browse |
| Bilibili | Blocks overseas/server IPs |

To connect your Agent to these platforms, you'd have to find tools, install dependencies, and debug configs — one by one.

**Agent Reach turns this into one command:**

```
Install Agent Reach: https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

Copy that to your Agent. 30 seconds later, it can read tweets, search Reddit, and watch Bilibili.

### ✅ Before you start, you might want to know

| | |
|---|---|
| 💰 **Completely free** | All tools are open source, all APIs are free. The only possible cost is a server proxy ($1/month) — local computers don't need one |
| 🔒 **Privacy safe** | Cookies stay local. Never uploaded. Fully open source — audit anytime |
| 🔄 **Kept up to date** | Upstream tools (yt-dlp, birdx, Jina Reader, etc.) are tracked and updated regularly |
| 🤖 **Works with any Agent** | Claude Code, OpenClaw, Cursor, Windsurf… any Agent that can run commands |
| 🩺 **Built-in diagnostics** | `agent-reach doctor` — one command shows what works, what doesn't, and how to fix it |

---

## Supported Platforms

| Platform | Capabilities | Setup | Notes |
|----------|-------------|:-----:|-------|
| 🌐 **Web** | Read | Zero config | Any URL → clean Markdown ([Jina Reader](https://github.com/jina-ai/reader) ⭐9.8K) |
| 🐦 **Twitter/X** | Read · Search | Zero config / Cookie | Single tweets readable out of the box. Cookie unlocks search, timeline, posting ([birdx](https://github.com/runesleo/birdx)) |
| 📕 **XiaoHongShu** | Read · Search · **Post · Comment · Like** | Cookie | Full functionality with browser cookie |
| 🔍 **Web Search** | Search | Free key | One key unlocks web + Reddit + Twitter search ([Exa](https://exa.ai), free 1000/month) |
| 📦 **GitHub** | Read · Search | Zero config | Public repos work immediately. `gh` CLI or token unlocks Fork, Issue, PR |
| 📺 **YouTube** | Read | Zero config | Subtitles from 1800+ video sites ([yt-dlp](https://github.com/yt-dlp/yt-dlp) ⭐148K) |
| 📺 **Bilibili** | Read | Zero config / Proxy | Video info + subtitles. Local works directly, servers need a proxy |
| 📡 **RSS** | Read | Zero config | Any RSS/Atom feed ([feedparser](https://github.com/kurtmckee/feedparser) ⭐2.3K) |
| 📖 **Reddit** | Search · Read | Free / Proxy | Search via Exa (free). Reading posts needs a proxy on servers. OAuth bot unlocks posting |

> **Setup levels:** Zero config = install and go · Free key = 30-second signup · Cookie = export from browser · Proxy = $1/month

---

## Get Started in 30 Seconds

Copy this to your AI Agent (Claude Code, OpenClaw, Cursor, etc.):

```
Install Agent Reach: https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

The Agent auto-installs, detects your environment, and tells you what's ready.

<details>
<summary>Manual install</summary>

```bash
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```
</details>

---

## Works Out of the Box

No configuration needed — just tell your Agent:

- "Read this link" → any web page
- "What's this GitHub repo about?" → repos, issues, code
- "What does this video cover?" → YouTube / Bilibili subtitles
- "Read this tweet" → Twitter posts
- "Subscribe to this RSS" → RSS / Atom feeds
- "Search GitHub for LLM frameworks" → GitHub search

**No commands to remember.** The Agent knows what to call.

---

## Unlock on Demand

Don't use it? Don't configure it. Every step is optional.

### 🔍 Search — Free, 30 seconds

Go to [exa.ai](https://exa.ai), sign up for a free key (1000 searches/month), and send it to your Agent. One key unlocks web search + Reddit search + Twitter search.

### 🍪 Cookies — Free, 2 minutes

Tell your Agent "help me configure Twitter cookies" or "set up XiaoHongShu" — it'll guide you through exporting from your browser. Local computers can auto-import.

### 🌐 Proxy — $1/month, servers only

Reddit and Bilibili block server IPs. Get a proxy ([Webshare](https://webshare.io) recommended, $1/month) and send the address to your Agent.

> Local computers don't need a proxy. Reddit search works free via Exa even without one.

---

## Status at a Glance

```
$ agent-reach doctor

👁️  Agent Reach Status
========================================

✅ Ready to use:
  ✅ GitHub repos and code — public repos readable and searchable
  ✅ Twitter/X tweets — readable. Cookie unlocks search and posting
  ✅ YouTube video subtitles — yt-dlp
  ⚠️  Bilibili video info — server IPs may be blocked, configure proxy
  ✅ RSS/Atom feeds — feedparser
  ✅ Web pages (any URL) — Jina Reader API

🔍 Search (free Exa key to unlock):
  ⬜ Web semantic search — sign up at exa.ai for free key

🔧 Configurable:
  ⬜ Reddit posts and comments — search via Exa (free). Reading needs proxy
  ⬜ XiaoHongShu notes — needs cookie. Export from browser

Status: 6/9 channels available
```

---

## Design Philosophy

**Agent Reach is a setup scaffold, not a framework.**

Every time you spin up a new Agent, you spend time finding tools, installing deps, and debugging configs — what reads Twitter? How do you bypass Reddit blocks? How do you extract YouTube subtitles? Every time, you re-do the same work.

Agent Reach does one simple thing: **it makes those tool selection and configuration decisions for you.**

| Scenario | Tool | Why |
|----------|------|-----|
| Read web pages | [Jina Reader](https://github.com/jina-ai/reader) | 9.8K stars, free, no API key needed |
| Read tweets | [birdx](https://github.com/runesleo/birdx) | Cookie auth, no $100/month official API |
| Extract subtitles | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 148K stars, 1800+ video sites |
| Search the web | [Exa](https://exa.ai) | AI semantic search, 1000 free/month |
| Read RSS | [feedparser](https://github.com/kurtmckee/feedparser) | Python ecosystem standard, 2.3K stars |

One file per platform, ~50 lines each. Swap any backend by editing one file — everything else stays untouched.

<details>
<summary>Project structure</summary>

```
agent_reach/channels/
├── web.py          → Jina Reader
├── twitter.py      → birdx
├── youtube.py      → yt-dlp
├── github.py       → GitHub API
├── bilibili.py     → Bilibili API
├── reddit.py       → Reddit JSON API
├── xiaohongshu.py  → XHS Web API
├── rss.py          → feedparser
└── exa_search.py   → Exa Search API
```
</details>

---

## Contributing

[Issues](https://github.com/Panniantong/agent-reach/issues) and [PRs](https://github.com/Panniantong/agent-reach/pulls) welcome.

Want to add a new platform? Copy any channel file, tweak it — each one is only ~50 lines.

## Credits

[Jina Reader](https://github.com/jina-ai/reader) · [yt-dlp](https://github.com/yt-dlp/yt-dlp) · [birdx](https://github.com/runesleo/birdx) · [Exa](https://exa.ai) · [feedparser](https://github.com/kurtmckee/feedparser)

## License

[MIT](../LICENSE)
