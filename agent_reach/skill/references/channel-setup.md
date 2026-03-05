# Channel Setup Guide

When user asks "帮我配 XXX" / "configure XXX", follow the steps below.

**Principle:** User only provides cookies. Everything else (install deps, start services, register MCP) is your job.

## ⚠️ Directory Rules

| Purpose | Directory |
|---------|-----------|
| Temporary output | `/tmp/` |
| Upstream tool repos | `~/.agent-reach/tools/` |
| Config & tokens | `~/.agent-reach/` |

**Never** create files in the agent workspace.

## Cookie Import (universal for all login-required platforms)

> ⚠️ Remind user: use a **dedicated secondary account**, not their main account.

1. User logs into the platform in their browser
2. Install [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) Chrome extension
3. Click extension → Export → Header String
4. User sends the string to you

Local computer users can also use `agent-reach configure --from-browser chrome` for auto-extraction.

---

## Twitter/X

**What you do:**
```bash
agent-reach configure twitter-cookies "USER_PASTED_COOKIES"
```

**What user does:** Export cookies from x.com via Cookie-Editor.

---

## 小红书 / XiaoHongShu

**Requires:** Docker

**What you do:**
```bash
# 1. Start MCP service
docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp

# On servers, add proxy to avoid IP blocking:
# docker run -d --name xiaohongshu-mcp -p 18060:18060 -e XHS_PROXY=http://user:pass@ip:port xpzouying/xiaohongshu-mcp

# 2. Register with mcporter
mcporter config add xiaohongshu http://localhost:18060/mcp
```

**What user does:** Export cookies from xiaohongshu.com via Cookie-Editor, send to you.

**Cookie install:** Write user's cookie string to the MCP service's cookie file.

Fallback: Local users can open http://localhost:18060 to scan QR code.

---

## 抖音 / Douyin

**No login needed.**

**What you do:**
```bash
# 1. Clone and install
mkdir -p ~/.agent-reach/tools && cd ~/.agent-reach/tools
git clone https://github.com/yzfly/douyin-mcp-server.git && cd douyin-mcp-server
pip install -e .

# 2. Start HTTP service (port 18070)
python -c "
from douyin_mcp_server.server import mcp
mcp.settings.host = '127.0.0.1'
mcp.settings.port = 18070
mcp.run(transport='streamable-http')
"

# 3. Register with mcporter
mcporter config add douyin http://localhost:18070/mcp
```

> For AI voice-to-text extraction, user needs SiliconFlow API Key (`export API_KEY="sk-xxx"`).

---

## LinkedIn

**Basic:** Jina Reader works for public pages (no setup needed): `curl -s "https://r.jina.ai/https://linkedin.com/in/username"`

**Full features (profiles, search):**

**What you do:**
```bash
pip install linkedin-scraper-mcp
```

**Login (requires browser window):**
- **Local (has desktop):** `linkedin-scraper-mcp --login --no-headless` → user logs in manually
- **Server (no UI):** Need VNC:
  ```bash
  apt install -y tigervnc-standalone-server
  vncserver :1 -geometry 1280x720
  export DISPLAY=:1
  linkedin-scraper-mcp --login --no-headless
  ```

**After login, start MCP service:**
```bash
linkedin-scraper-mcp --transport streamable-http --port 8001
mcporter config add linkedin http://localhost:8001/mcp
```

---

## Boss直聘

**Basic:** Jina Reader works for job pages: `curl -s "https://r.jina.ai/https://www.zhipin.com/job_detail/xxx"`

**Full features (search, greet HR):**

**What you do:**
```bash
mkdir -p ~/.agent-reach/tools && cd ~/.agent-reach/tools
git clone https://github.com/mucsbr/mcp-bosszp.git && cd mcp-bosszp
pip install -r requirements.txt && playwright install chromium
```

**Login (QR code scan):**
```bash
# 1. Start service
python boss_zhipin_fastmcp_v2.py

# 2. Trigger QR code
mcporter call 'bosszhipin.start_login()'

# 3. User scans QR code with Boss直聘 app
```

---

## Proxy (for server users)

Reddit, Bilibili, XiaoHongShu may block server IPs.

```bash
agent-reach configure proxy http://user:pass@ip:port
```

Recommend Webshare (~$1/month).

---

## Verify

After any setup, always run:
```bash
agent-reach doctor
```
