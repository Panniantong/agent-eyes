# Social

## Bluesky

Public read-only search:

```powershell
agent-reach collect --channel bluesky --operation search --input "OpenAI" --limit 10 --json
```

## Twitter/X

This channel is optional and cookie-based.

Install path:

```powershell
agent-reach install --channels=twitter
```

Configure cookies:

```powershell
agent-reach configure twitter-cookies "auth_token=...; ct0=..."
```

Validate live readiness before depending on Twitter/X search:

```powershell
agent-reach doctor --json --probe
```

`twitter status` confirms authentication, but it does not guarantee that live search still works.

Or import them from a local browser:

```powershell
agent-reach configure --from-browser chrome
```

Basic usage:

```powershell
agent-reach collect --channel twitter --operation search --input "gpt-5.4" --limit 10 --json
agent-reach collect --channel twitter --operation user --input "openai" --json
agent-reach collect --channel twitter --operation user_posts --input "openai" --limit 50 --json
agent-reach collect --channel twitter --operation tweet --input "https://x.com/OpenAI/status/2042296046009626989" --limit 20 --json
agent-reach collect --channel twitter --operation search --input "from:openai has:media type:photos" --limit 50 --json
twitter status
twitter user openai --json
twitter user-posts openai -n 50 --json
twitter search --from openai --has images --type photos -n 50 --json
twitter search "gpt-5.4" -n 10
twitter tweet "https://x.com/openai/status/123"
```

For account analysis, prefer these in order:

- `user` for profile metadata
- `user_posts` for recent posts by a single account
- `search` with `from:handle`, `has:media`, and `type:photos` when you want media-heavy subsets

Plain free-text `search "OpenAI"` may return related discussion rather than only `@OpenAI` posts.
