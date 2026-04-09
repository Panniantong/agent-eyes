# Troubleshooting

## `doctor` says GitHub is not authenticated

Run:

```powershell
gh auth login
```

Or store a token explicitly:

```powershell
agent-reach configure github-token YOUR_TOKEN
```

For non-interactive environments, `GITHUB_TOKEN` also works.

## `doctor` says Twitter/X is not authenticated

Run one of:

```powershell
agent-reach configure twitter-cookies "auth_token=...; ct0=..."
agent-reach configure --from-browser chrome
```

For browser import, close the browser first and make sure you are already logged into `x.com`.

For non-interactive environments, set:

```powershell
$env:TWITTER_AUTH_TOKEN = "..."
$env:TWITTER_CT0 = "..."
```

## `doctor` says Exa is not configured

Run:

```powershell
mcporter --config "$HOME\.mcporter\mcporter.json" config add exa https://mcp.exa.ai/mcp
```

## `doctor` says YouTube needs a JS runtime

Install Node.js LTS with `winget`, then run the fix command printed by `doctor`.

## `collect --json` returns `command_failed`

Run:

```powershell
agent-reach doctor --json
agent-reach doctor --json --probe
```

If the affected channel is optional, confirm its backend directly:

```powershell
gh auth status
twitter status
yt-dlp --version
mcporter --config "$HOME\.mcporter\mcporter.json" config list
```

## `collect --json` returns `invalid_response`

This usually means the upstream CLI or HTTP reader returned an unexpected payload. Re-run the same collection once, then inspect the backend directly:

```powershell
agent-reach collect --channel github --operation read --input "openai/openai-python" --json
gh repo view openai/openai-python --json name,nameWithOwner,url
```
