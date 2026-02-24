# Agent Reach — Installation Guide

## For Humans

Copy this to your AI Agent:

```
帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

---

## For AI Agents

**Important: You are an AI Agent with problem-solving abilities. If any step below fails, don't just report the error — diagnose and fix it yourself. You have shell access, you can search for solutions, try alternative install methods, and debug issues. Only ask the user when you genuinely need their input (API keys, cookies, passwords).**

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

### Troubleshooting (self-fix before asking the user)

If `agent-reach install` shows warnings or failures, try fixing them yourself:

| Problem | What you can do |
|---------|----------------|
| `pip install` fails with `--break-system-packages` | Add the flag: `pip install --break-system-packages ...` or create a venv first |
| `npm install -g mcporter` timeout | Retry with longer timeout, or try: `npx mcporter@latest list` (uses npx without global install) |
| `gh` CLI install fails | Try: `conda install gh`, `snap install gh`, or download binary from https://github.com/cli/cli/releases |
| `node`/`npm` not found after install | Check `export PATH` or try: `apt install nodejs npm` / `brew install node` |
| `mcporter config add exa` fails | Run manually: `mcporter config add exa https://mcp.exa.ai/mcp` |
| `yt-dlp` not found | `pip install yt-dlp` or `pip3 install yt-dlp` |
| `birdx` not found | `pip install birdx` — optional, Twitter reading still works without it |
| Permission denied | Run with `sudo` or fix directory permissions |
| Any Python package conflict | Create a venv: `python3 -m venv ~/agent-reach-env && source ~/agent-reach-env/bin/activate` then reinstall |

**General principle: You're a capable AI Agent. If a tool fails to install via one method, try another. Check error messages, search for solutions, and iterate. Don't give up after one attempt.**

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
