# Agent Eyes — Installation Guide

## For Humans

Copy this to your AI Agent:

```
Install Agent Eyes: https://raw.githubusercontent.com/Panniantong/agent-eyes/main/docs/install.md
```

---

## For AI Agents

Install Agent Eyes with minimal user effort. Goal: fewest questions, fewest steps.

### Step 1: Install and detect

```bash
pip install git+https://github.com/Panniantong/agent-eyes.git || pip3 install git+https://github.com/Panniantong/agent-eyes.git
agent-eyes install --env=auto
```

Read the output. It tells you the detected environment (local/server) and what's already working.

### Step 2: Set up cookies (the approach depends on environment)

#### Path A: Local computer (auto-detected)

Offer one-click import:

> "I can grab your browser cookies automatically to unlock Twitter, XiaoHongShu, and Bilibili — all at once. Just close Chrome first, then say 'go'."

If user agrees:
```bash
pip install browser-cookie3 2>/dev/null; agent-eyes configure --from-browser chrome
```

If user uses another browser: replace `chrome` with `firefox`, `edge`, `brave`, or `opera`.

If it fails or user declines, fall through to Path B.

#### Path B: Server, or auto-import didn't work

Tell the user the easiest manual method:

> "I need cookies from your browser to unlock some platforms. Here's the fastest way (30 seconds per site):
>
> 1. Install the **Cookie-Editor** Chrome extension: https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
> 2. Go to the site (e.g. x.com) — make sure you're logged in
> 3. Click the Cookie-Editor icon → **Export** → **Header String**
> 4. Paste the result to me
>
> Which platforms do you use? I'll tell you which ones to export."

For each platform the user wants:

**Twitter/X** — export from https://x.com :
```bash
agent-eyes configure twitter-cookies "PASTED_COOKIE_STRING"
```
(Accepts both: full cookie string OR just `auth_token ct0` as two values)

**XiaoHongShu** — export from https://www.xiaohongshu.com :
```bash
agent-eyes configure xhs-cookie "PASTED_COOKIE_STRING"
```

**Bilibili** — export from https://www.bilibili.com :
(On local computers Bilibili already works without cookies. On servers it needs a proxy — see Step 4.)

### Step 3: Set up search

> "Want to unlock web search? One free API key lets me search the web, Reddit, and Twitter.
> Go to https://exa.ai → sign up (free, 1000 searches/month) → send me the key.
> Or say 'skip' — everything else still works."

```bash
agent-eyes configure exa-key THE_KEY
```

### Step 4: Server-only — proxy for Reddit/Bilibili

Only mention if environment was detected as server:

> "On servers, Reddit and Bilibili block direct access. Reddit *search* still works via Exa (free), but for reading full Reddit posts or using Bilibili, you'd need a residential proxy (~$1/month).
> Get one at https://webshare.io if you want. Or skip — not required."

```bash
agent-eyes configure proxy http://user:pass@ip:port
```

### Step 5: Done

```bash
agent-eyes doctor
```

> "✅ All set! [list active channels]. Try: 'search Reddit for ...' or 'read this URL'"

Users can configure more channels anytime — just say "set up Twitter" or "add proxy".

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `agent-eyes configure --from-browser chrome` | Auto-import ALL cookies at once (local only) |
| `agent-eyes configure exa-key KEY` | Unlock search (web + Reddit + Twitter) |
| `agent-eyes configure twitter-cookies "COOKIE_STRING"` | Unlock Twitter (cookie string or auth_token + ct0) |
| `agent-eyes configure xhs-cookie "COOKIE_STRING"` | Unlock XiaoHongShu |
| `agent-eyes configure youtube-cookies chrome` | Unlock age-restricted YouTube |
| `agent-eyes configure proxy URL` | Unlock Reddit reader + Bilibili (server) |
| `agent-eyes doctor` | Show all channels and their status |
| `agent-eyes read URL` | Read any URL |
| `agent-eyes search "query"` | Search the web |
