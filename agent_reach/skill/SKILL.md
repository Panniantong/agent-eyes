---
name: agent-reach
description: Windows-first research integration tooling for Codex. Use when the user needs to inspect available research channels, verify readiness, export Codex integration settings, or run thin read-only collection over web, Exa, GitHub, Hatena Bookmark, Bluesky, Qiita, YouTube, RSS, or optional Twitter/X.
---

# Agent Reach

Use this skill when the task benefits from Agent Reach's Windows/Codex integration surface.

## Positioning

This fork is intentionally narrow. Treat it as:

- a bootstrapper for the local research toolchain
- a machine-readable channel registry
- a readiness and diagnostics layer
- an integration helper for downstream projects
- a thin read-only collection surface

Do not assume this fork owns scheduling, ranking, summarization, or publishing. Those remain responsibilities of the host project.

## Discovery First

Start with the integration surface before reaching for backend-specific commands.

```powershell
agent-reach channels --json
agent-reach doctor --json
agent-reach doctor --json --probe
agent-reach collect --channel github --operation read --input "openai/openai-python" --json
agent-reach export-integration --client codex --format json
```

## Supported channels

- `web`: generic page reading through Jina Reader
- `exa_search`: wide web search through `mcporter`
- `github`: repository and code search through `gh`
- `hatena_bookmark`: URL-centric Hatena Bookmark reactions and related entries
- `bluesky`: public Bluesky post search
- `qiita`: public Qiita article search
- `youtube`: metadata and subtitle extraction through `yt-dlp`
- `rss`: RSS and Atom feeds through `feedparser`
- `twitter`: optional Twitter/X search through `twitter-cli`

## Workflow

1. Run `agent-reach channels --json` if the available surfaces are unclear.
2. Run `agent-reach doctor --json` when readiness matters.
3. Use `--probe` only when a lightweight live check is useful.
4. Use `agent-reach collect --json` by default when external code needs normalized results.
5. Use `AgentReachClient` only when the host Python environment has Agent Reach installed into it directly.
6. Use `qiita` for direct Qiita article search. Use `hatena_bookmark` when the input is a URL and you want Hatena reactions or related entries.
7. Use `bluesky` for public Bluesky post search.
8. Prefer `exa_search` plus `web` for note, Zenn, blogs, docs sites, and other general web discovery.
9. Treat Twitter/X as opt-in and expect cookie-based auth.

## Command Routing

- General search: read [references/search.md](references/search.md)
- GitHub work: read [references/dev.md](references/dev.md)
- Web pages and RSS: read [references/web.md](references/web.md)
- YouTube: read [references/video.md](references/video.md)
- Twitter/X: read [references/social.md](references/social.md)
