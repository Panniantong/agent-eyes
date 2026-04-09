# Agent Reach

Windows-first research integration tooling with a stable Python SDK and JSON CLI for downstream projects.

Agent Reach is intentionally narrow. It is designed to help other tools collect information safely and predictably, not to own scheduling, ranking, summarization, or posting. In practice this fork does four jobs:

- bootstrap the Windows-friendly toolchain needed for research workflows
- expose a stable registry of supported channels
- provide readiness diagnostics and integration exports
- offer a thin read-only collection surface for external apps, bots, and CI jobs

## Supported channels

- `web` via Jina Reader
- `exa_search` via Exa MCP and `mcporter`
- `github` via `gh`
- `youtube` via `yt-dlp`
- `rss` via `feedparser`
- optional `twitter` via `twitter-cli`

## Install

```powershell
uv tool install .
agent-reach install --env=auto
```

Preview the Windows commands without changing anything:

```powershell
agent-reach install --env=auto --safe
agent-reach install --env=auto --dry-run --json
```

Optional Twitter/X support:

```powershell
agent-reach install --env=auto --channels=twitter
agent-reach configure twitter-cookies "auth_token=...; ct0=..."
```

## Public surfaces

Python SDK:

```python
from agent_reach import AgentReachClient

client = AgentReachClient()
result = client.github.read("openai/openai-python")
print(result["items"][0]["title"])
```

CLI JSON:

```powershell
agent-reach collect --channel github --operation read --input "openai/openai-python" --json
agent-reach collect --channel exa_search --operation search --input "latest gpt-5.4 release notes" --limit 3 --json
```

Discovery and diagnostics:

```powershell
agent-reach channels --json
agent-reach doctor --json
agent-reach doctor --json --probe
agent-reach export-integration --client codex --format json
agent-reach check-update --json
```

These are the supported machine-readable entry points for external projects. They are designed so bots, GitHub Actions, and other codebases do not need to scrape README text or SKILL.md.

## Typical downstream use

- Python apps and Discord bots call `AgentReachClient`
- GitHub Actions and other non-Python jobs call `agent-reach collect --json`
- setup tooling calls `agent-reach channels --json`, `doctor --json`, and `export-integration`

Agent Reach normalizes results into `items`, keeps the backend-native payload in `raw`, and never prompts interactively during collection.

## Guides

- Install guide: [docs/install.md](docs/install.md)
- Python SDK: [docs/python-sdk.md](docs/python-sdk.md)
- Codex integration: [docs/codex-integration.md](docs/codex-integration.md)
- Codex compatibility: [docs/codex-compatibility.md](docs/codex-compatibility.md)
- Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)

## What `install` does on Windows

- installs `gh` with `winget`
- installs `yt-dlp` with `winget`
- uses the existing `node`/`npm` install, or installs Node.js LTS with `winget`
- installs `mcporter` with `npm install -g mcporter`
- registers Exa in the user config with `mcporter --config "$HOME\\.mcporter\\mcporter.json" config add exa https://mcp.exa.ai/mcp`
- writes the `yt-dlp` JS runtime config for Node.js
- installs the bundled skill into `CODEX_HOME/skills`, `~/.codex/skills`, or `~/.agents/skills`

## Integration artifacts

This repo ships integration-oriented artifacts directly:

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `agent_reach/skill/`

These artifacts exist to make downstream composition easier. Scheduling, message formatting, and publishing remain responsibilities of the host project.
