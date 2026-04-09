# Agent Reach Codex Integration

Agent Reach is a Windows-first integration layer for research tooling. It now exposes a thin read-only collection surface, while keeping scheduling and publishing outside the repo.

## What it provides

- a stable channel registry through `agent-reach channels --json`
- readiness diagnostics through `agent-reach doctor --json`
- a thin read-only collector through `agent-reach collect --json`
- a non-mutating Codex export through `agent-reach export-integration --client codex`
- repo-local Codex artifacts through `.codex-plugin/plugin.json` and `.mcp.json`

## Recommended flow

```powershell
agent-reach channels --json
agent-reach doctor --json --probe
agent-reach collect --channel github --operation read --input "openai/openai-python" --json
agent-reach export-integration --client codex --format json
```

## Repo artifacts

- Plugin manifest: `.codex-plugin/plugin.json`
- MCP config snippet: `.mcp.json`
- Bundled skill source: `agent_reach/skill`
- Python SDK docs: `docs/python-sdk.md`

## Supported channels

- `web`
- `exa_search`
- `github`
- `youtube`
- `rss`
- `twitter` (optional)

These channels are exposed as metadata, setup guidance, diagnostics, and read-only collection operations so downstream tools can wire their own workflows without scraping repo docs.
