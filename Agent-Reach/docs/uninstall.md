# Agent Reach — Uninstall Guide

## For Humans

Copy this to your AI Agent:

```
帮我卸载 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/uninstall.md
```

---

## For AI Agents

### Goal

Completely remove Agent Reach and its optional dependencies from the user's machine. Clean up config files if the user wants.

### ⚠️ Boundaries

- **DO NOT** run commands with `sudo` unless the user explicitly approved
- **DO NOT** remove tools that weren't installed by Agent Reach (e.g. if the user had `gh` CLI before Agent Reach, don't remove it)
- **ASK** before deleting config files — they may contain credentials the user wants to keep
- If unsure whether a dependency was pre-existing, **skip it** and tell the user

---

### Step 1: Uninstall the Python package

```bash
pip uninstall agent-reach -y
```

---

### Step 2: Ask about config files

Ask the user:

> "要不要一起删掉配置文件？配置文件里存着你的 Cookie、代理地址等信息，删了之后重新安装需要重新配置。"

If yes:

```bash
rm -rf ~/.agent-reach/
```

If no, skip this step.

---

### Step 3: Ask about optional dependencies

Agent Reach may have installed these tools. Ask the user if they want to remove them:

> "Agent Reach 安装时可能装了以下工具，要一起删掉吗？如果你在其他地方也用到了这些工具，建议保留。"

**bird CLI** (Twitter):
```bash
npm uninstall -g @steipete/bird
```

**mcporter** (Exa search):
```bash
npm uninstall -g mcporter
```

**undici** (Twitter proxy support):
```bash
npm uninstall -g undici
```

**yt-dlp** (YouTube / Bilibili) — installed as a Python package, removed with agent-reach in Step 1. If installed separately:
```bash
pip uninstall yt-dlp -y
```

**instaloader** (Instagram):
```bash
pip uninstall instaloader -y
```

**gh CLI** (GitHub) — only remove if the user confirms they don't use it for anything else:
```bash
# macOS
brew uninstall gh

# Linux (apt)
sudo apt remove gh
```

**Docker containers** (XiaoHongShu):
```bash
docker stop xiaohongshu-mcp && docker rm xiaohongshu-mcp
```

---

### Step 4: Confirm

Run a quick check to confirm the package is gone:

```bash
pip show agent-reach 2>&1 || echo "agent-reach uninstalled successfully"
```

Report the result to the user.

---

## Quick Reference

| What to remove | Command |
|----------------|---------|
| Agent Reach package | `pip uninstall agent-reach -y` |
| Config & credentials | `rm -rf ~/.agent-reach/` |
| bird CLI (Twitter) | `npm uninstall -g @steipete/bird` |
| mcporter (Exa search) | `npm uninstall -g mcporter` |
| undici (proxy support) | `npm uninstall -g undici` |
| instaloader (Instagram) | `pip uninstall instaloader -y` |
| XiaoHongShu container | `docker stop xiaohongshu-mcp && docker rm xiaohongshu-mcp` |
