# Search

## Search Surfaces

Use the globally installed `agent-reach` CLI from the current project. Do not copy Agent Reach files into the project just to search.

Exa is available for broad web discovery when `mcporter` is ready.

```powershell
agent-reach collect --channel exa_search --operation search --input "latest o3 vs gpt-5.4" --limit 5 --json
```

SearXNG is available when a SearXNG instance is configured by the caller:

```powershell
agent-reach configure searxng-base-url "https://searx.example.org"
agent-reach collect --channel searxng --operation search --input "latest agent tools" --limit 5 --json
```

For Qiita:

```powershell
agent-reach collect --channel qiita --operation search --input "python user:Qiita" --limit 5 --json
```

For note, Zenn, docs, and blogs:

1. Search with Exa.
2. Open the chosen result with Jina Reader.

```powershell
agent-reach collect --channel web --operation read --input "https://example.com/article" --json
```

If you need to debug Exa directly, fall back to:

```powershell
mcporter --config "$HOME\.mcporter\mcporter.json" call exa.web_search_exa --args "{\"query\":\"latest o3 vs gpt-5.4\",\"numResults\":5}" --output json
```

For Hatena Bookmark URL reactions:

```powershell
agent-reach collect --channel hatena_bookmark --operation read --input "https://example.com" --limit 5 --json
```

For Hacker News:

```powershell
agent-reach collect --channel hacker_news --operation search --input "agent frameworks" --limit 5 --json
agent-reach collect --channel hacker_news --operation top --input "top" --limit 5 --json
```

For MCP Registry discovery:

```powershell
agent-reach collect --channel mcp_registry --operation search --input "docs mcp" --limit 5 --json
agent-reach collect --channel mcp_registry --operation read --input "ac.tandem/docs-mcp" --json
```

## Larger Research Runs

Use bounded fan-out:

1. Run 2-4 broad `exa_search` queries with small limits.
2. Dedupe URLs or IDs before deeper reads.
3. Use specialist channels for high-signal sources such as GitHub, Qiita, Bluesky, RSS, YouTube, Hatena Bookmark, Hacker News, MCP Registry, Reddit, or SearXNG when they match the task and are ready.
4. Run `web read` only on selected URLs.
5. Save the JSON envelopes when downstream ranking, summarization, or Discord publishing needs traceability.

Recommended limits:

- broad discovery: `--limit 5` to `--limit 10`
- source-specific search: `--limit 10` to `--limit 20`
- deep reads per round: around 10 selected URLs
