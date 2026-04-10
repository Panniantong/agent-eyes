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

YouTube collection returns video metadata, subtitle/caption availability, and thumbnail references. It does not download video binaries, extract frames, run OCR, or transcribe audio.

## `doctor --json` returns success even when optional channels are off

This is expected with the default `--exit-policy core`. Tier 0 channel failures affect the exit code; optional setup gaps are reported in `summary.advisory_not_ready`.

Use strict mode when automation requires every optional channel to be ready:

```powershell
agent-reach doctor --json --exit-policy all
```

## `doctor` says Crawl4AI is not installed

Install Crawl4AI into the Python environment that needs browser-backed reads:

```powershell
uv pip install "agent-reach[crawl4ai] @ git+https://github.com/iwachacha/Agent-Reach.git"
python -m playwright install chromium
```

For checkout development, use `uv pip install -e .[crawl4ai]` instead.

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

## Twitter/X search returns `not_found` or HTTP 404

Run:

```powershell
agent-reach doctor --json --probe
agent-reach collect --channel twitter --operation user --input "openai" --json
agent-reach collect --channel twitter --operation search --input "OpenAI" --limit 1 --json
```

`twitter status` only proves that the session is authenticated. Twitter/X search can still fail even when profile lookups succeed. If `user` works but `search` fails, treat the search backend as not ready and avoid advertising Twitter/X search as available in downstream automation.

## Raw `twitter --help` fails with `UnicodeEncodeError` on Windows

PowerShell's default legacy code page can make `twitter-cli` crash while rendering help text. Run the raw backend CLI with UTF-8 enabled:

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
twitter --help
```

Agent Reach sets these environment variables when it invokes backend commands, so this mainly affects manual fallback debugging.
