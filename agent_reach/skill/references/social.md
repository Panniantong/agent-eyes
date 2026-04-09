# Twitter/X

This channel is optional and cookie-based.

Install path:

```powershell
agent-reach install --channels=twitter
```

Configure cookies:

```powershell
agent-reach configure twitter-cookies "auth_token=...; ct0=..."
```

Or import them from a local browser:

```powershell
agent-reach configure --from-browser chrome
```

Basic usage:

```powershell
agent-reach collect --channel twitter --operation search --input "gpt-5.4" --limit 10 --json
twitter status
twitter search "gpt-5.4" -n 10
twitter tweet "https://x.com/openai/status/123"
```
