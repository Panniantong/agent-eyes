# Agent Reach — Installation Guide

## For Humans

Copy this to your AI Agent:

```
帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

---

## For AI Agents

### Step 1: Install

```bash
pip install https://github.com/Panniantong/agent-reach/archive/main.zip || pip3 install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

This single command does everything automatically:
- Installs system dependencies (gh CLI, Node.js, mcporter) if missing
- Configures Exa search (free, no API key needed)
- Detects local computer vs server
- Auto-imports browser cookies on local (Twitter)
- Tests all channels
- Shows what's working and what needs setup

**Read the output carefully.** It tells you exactly what happened and what's next.

### Step 2: Only if needed — configure what's missing

Based on the install output, you may need to configure one or two things.
Only ask the user for items the install output says are missing.

**If cookies were not auto-imported (server users):**
> "To unlock Twitter search and posting, install the Cookie-Editor Chrome extension, go to twitter.com, click Export → Header String, and paste it to me."
> Extension: https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm

```bash
agent-reach configure twitter-cookies "PASTED_STRING"
```

**If on server and wants Reddit/Bilibili full access:**
> "Reddit and Bilibili block server IPs. Get a proxy at https://webshare.io ($1/month) and send me the address."

```bash
agent-reach configure proxy http://user:pass@ip:port
```

### Step 3: Verify

```bash
agent-reach doctor
```

Report what's active. Users can configure more anytime by asking.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `agent-reach install --env=auto` | Full auto-setup (installs deps + configures) |
| `agent-reach doctor` | Show status |
| `agent-reach configure twitter-cookies "..."` | Unlock Twitter search + posting |
| `agent-reach configure proxy URL` | Unlock Reddit + Bilibili (server) |
| `agent-reach read URL` | Read any URL |
| `agent-reach search "query"` | Search the web |
