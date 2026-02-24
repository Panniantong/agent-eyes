# 👁️ Agent Eyes

**Give your AI Agent eyes to see the entire internet.**

Agent Eyes is infrastructure for the Agent world — install once, and your AI Agent can search and read content across 10+ platforms. Zero to minimal configuration.

> *Built on top of [x-reader](https://github.com/runesleo/x-reader) by [@runes_leo](https://x.com/runes_leo) — thank you for the amazing open-source work. 🙏*

---

## Why Agent Eyes?

AI Agents are powerful, but blind. They can't browse Reddit, search Twitter, or read WeChat articles. Agent Eyes fixes that.

- **One install, 10+ platforms** — web pages, GitHub, Reddit, Twitter, YouTube, Bilibili, WeChat, XiaoHongShu, RSS, Telegram
- **Search + Read** — not just URL extraction, but actual search capability (find, then read)
- **Agent-native design** — CLI, MCP Server, Python API — works with any AI Agent platform
- **Mostly free** — 99% of features cost nothing. One free API key unlocks full search.

---

## Quick Start

```bash
# Install
pip install git+https://github.com/Panniantong/agent-eyes.git

# Check what's available
agent-eyes doctor

# Read any URL (works immediately, no config needed)
agent-eyes read "https://github.com/openai/gpt-4"
agent-eyes read "https://www.bilibili.com/video/BV1xx411c7mD"

# Search GitHub (works immediately, no config needed)
agent-eyes search-github "LLM framework"

# Unlock search (one free API key)
agent-eyes setup
agent-eyes search "AI agent infrastructure 2025"
agent-eyes search-reddit "best self-hosted LLM" --sub LocalLLaMA
agent-eyes search-twitter "OpenClaw agent"
```

---

## Platform Support

### ✅ Zero Config (works out of the box)

| Platform | Read | Search | Notes |
|----------|:----:|:------:|-------|
| Web Pages | ✅ | — | Any URL via Jina Reader |
| GitHub | ✅ | ✅ | Repos, issues, PRs, code |
| Bilibili | ✅ | — | Videos with subtitles |
| YouTube | ✅ | — | Videos with subtitles (needs yt-dlp) |
| RSS | ✅ | — | Any RSS/Atom feed |
| Single Tweet | ✅ | — | Via Jina Reader |

### 🔑 One Free API Key (30 seconds to set up)

| Platform | Read | Search | Notes |
|----------|:----:|:------:|-------|
| Web (semantic) | — | ✅ | Exa API (1000 free/month) |
| Reddit | — | ✅ | Via Exa (site:reddit.com) |
| Twitter/X | — | ✅ | Via Exa (site:x.com) |

### ⚙️ Optional Setup

| Platform | Read | Search | What's Needed |
|----------|:----:|:------:|---------------|
| Reddit (full) | ✅ | — | ISP proxy (~$3-10/mo) |
| Twitter (advanced) | ✅ | ✅ | birdx + browser cookies (free) |
| WeChat Articles | ✅ | — | Playwright (free, auto-installed) |
| XiaoHongShu | ✅ | — | Playwright + one-time login (free) |
| Video Transcription | ✅ | — | Groq API key (free) |

---

## Three Ways to Use

### 1. Command Line (CLI)

```bash
agent-eyes read <url>                    # Read any URL
agent-eyes search "query"                # Search the web
agent-eyes search-reddit "query"         # Search Reddit
agent-eyes search-github "query"         # Search GitHub
agent-eyes search-twitter "query"        # Search Twitter
agent-eyes setup                         # Interactive setup wizard
agent-eyes doctor                        # Check platform status
```

### 2. MCP Server (for Claude Code, Cursor, etc.)

```bash
pip install agent-eyes[mcp]
python -m agent_eyes.integrations.mcp_server
```

Exposes 8 tools: `read_url`, `read_batch`, `detect_platform`, `search`, `search_reddit`, `search_github`, `search_twitter`, `get_status`

Add to your MCP config:

```json
{
  "mcpServers": {
    "agent-eyes": {
      "command": "python",
      "args": ["-m", "agent_eyes.integrations.mcp_server"]
    }
  }
}
```

### 3. Python Library

```python
from agent_eyes import AgentEyes
import asyncio

eyes = AgentEyes()

# Read
result = asyncio.run(eyes.read("https://github.com/openai/gpt-4"))
print(result["title"])
print(result["content"])

# Search
results = asyncio.run(eyes.search("AI agent framework"))
for r in results:
    print(f"{r['title']} — {r['url']}")

# Search Reddit
results = asyncio.run(eyes.search_reddit("best LLM", subreddit="LocalLLaMA"))

# Health check
print(eyes.doctor_report())
```

---

## Configuration

### Interactive Setup

```bash
agent-eyes setup
```

Walks you through configuring each platform step by step. Only asks for what you want to set up.

### Agent-Readable Guides

Each platform has a detailed setup guide in `agent_eyes/guides/`. These are designed for AI Agents to read and follow — the Agent handles the technical steps, and only asks the user for things that require human action (logging in, copying API keys, buying proxies).

| Guide | What It Configures |
|-------|-------------------|
| `setup-exa.md` | Exa search API key (free) |
| `setup-reddit.md` | Reddit ISP proxy |
| `setup-twitter.md` | Twitter birdx cookies |
| `setup-xiaohongshu.md` | XiaoHongShu login |
| `setup-wechat.md` | WeChat Playwright |
| `setup-groq.md` | Groq Whisper API key (free) |

### Manual Config

Config file: `~/.agent-eyes/config.yaml`

```yaml
exa_api_key: "exa-..."
github_token: "ghp_..."
reddit_proxy: "http://user:pass@ip:port"
groq_api_key: "gsk_..."
```

Environment variables also work (uppercase): `EXA_API_KEY`, `GITHUB_TOKEN`, etc.

---

## Health Check

```bash
$ agent-eyes doctor

👁️  Agent Eyes Status
========================================

✅ Ready (no setup needed):
  ✅ Web Pages
  ✅ GitHub
  ✅ Bilibili
  ✅ RSS
  ✅ Tweet (single)
  ✅ GitHub Search

🔍 Search (need free Exa API key):
  ⬜ Web Search
  ⬜ Reddit Search
  ⬜ Twitter Search

🔧 Optional (advanced setup):
  ⬜ Twitter Advanced — Install birdx for timeline/deep search
  ⬜ Reddit Reader — Need proxy for full post reading
  ⬜ WeChat — pip install agent-eyes[browser]
  ⬜ XiaoHongShu — pip install agent-eyes[browser]

Status: 7/13 platforms active
Run `agent-eyes setup` to unlock more!
```

---

## Architecture

Agent Eyes is **not** a fork of x-reader. It's a layer built on top of it.

```
┌──────────────────────────────────────┐
│         Agent Eyes                    │
│  ┌──────────┐  ┌──────────────────┐  │
│  │  Search   │  │  Config + Doctor │  │
│  │  Exa      │  │  Setup Wizard   │  │
│  │  Reddit   │  │  Health Check   │  │
│  │  GitHub   │  │                 │  │
│  │  Twitter  │  │  Agent Guides   │  │
│  └──────────┘  └──────────────────┘  │
│  ┌──────────────────────────────────┐│
│  │  Readers (based on x-reader)     ││
│  │  Web · GitHub · Reddit · Twitter ││
│  │  YouTube · Bilibili · WeChat     ││
│  │  XHS · RSS · Telegram            ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │  Integrations                    ││
│  │  CLI · MCP Server · OpenClaw Skill│
│  └──────────────────────────────────┘│
└──────────────────────────────────────┘
```

- **Readers**: Content extraction from URLs (internalized from x-reader, MIT license)
- **Search**: Semantic search across platforms (Agent Eyes original)
- **Config + Doctor**: Configuration management and health checks (Agent Eyes original)
- **Integrations**: CLI, MCP Server, OpenClaw Skill (Agent Eyes original)

---

## Credits

- **[x-reader](https://github.com/runesleo/x-reader)** by [@runes_leo](https://x.com/runes_leo) — the URL-to-content extraction engine that Agent Eyes is built upon. MIT License.
- **[Exa](https://exa.ai)** — semantic search API powering web/Reddit/Twitter search.
- **[birdx](https://github.com/runesleo/birdx)** — Twitter CLI tool for advanced Twitter features.

## License

MIT
