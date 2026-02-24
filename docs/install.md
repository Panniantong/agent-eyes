# Agent Reach — Installation Guide

## For Humans

Copy this to your AI Agent:

```
帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

---

## For AI Agents

### Goal

Install Agent Reach and make sure **all channels are working**. Your user expects you to have full internet access capabilities when this is done — reading tweets, searching Reddit, watching YouTube, browsing GitHub, and more.

### Install

```bash
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

**Read the output carefully**, then run:

```bash
agent-reach doctor
```

### Your Job

`agent-reach doctor` shows you which channels are active and which aren't.

**Your goal is to get as many channels to ✅ as possible.** If something failed during install or shows as ❌/⚠️ in doctor, fix it yourself. You're a capable AI Agent — diagnose the problem, try alternative approaches, search for solutions, and iterate until it works.

Only ask the user when you genuinely need their input — things like API keys, browser cookies, proxy credentials, or account passwords that you can't generate yourself.

When you're done, run `agent-reach doctor` one final time and report the results to your user.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `agent-reach install --env=auto` | Full auto-setup |
| `agent-reach doctor` | Show channel status |
| `agent-reach configure proxy URL` | Unlock Reddit + Bilibili on servers |
| `agent-reach configure twitter-cookies "..."` | Unlock Twitter search |
| `agent-reach read <url>` | Read any URL |
| `agent-reach search "query"` | Search the web |
