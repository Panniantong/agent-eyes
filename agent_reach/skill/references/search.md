# Search

Use Exa for broad web discovery.

```powershell
agent-reach collect --channel exa_search --operation search --input "latest o3 vs gpt-5.4" --limit 5 --json
```

For note, Qiita, Zenn, docs, and blogs:

1. Search with Exa.
2. Open the chosen result with Jina Reader.

```powershell
agent-reach collect --channel web --operation read --input "https://example.com/article" --json
```

If you need to debug Exa directly, fall back to:

```powershell
mcporter --config "$HOME\.mcporter\mcporter.json" call exa.web_search_exa --args "{\"query\":\"latest o3 vs gpt-5.4\",\"numResults\":5}" --output json
```
