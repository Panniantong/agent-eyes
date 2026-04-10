# Downstream Usage

Agent Reach is designed to be used from other projects without copying this repository's files into them.

Use one of these integration modes:

- `agent-reach` CLI: best for Codex sessions, GitHub Actions, bots, and any project that can shell out to a stable JSON command.
- `AgentReachClient`: best when the host Python environment intentionally depends on Agent Reach as a package.
- Codex skill install: best for local Codex usage across many projects. The skill is installed once under the user's Codex home, not into each downstream repo.

## Codex Without Project Files

Install the tool and global skill once:

```powershell
uv tool install --force git+https://github.com/iwachacha/Agent-Reach.git
agent-reach skill --install
agent-reach version
agent-reach doctor --json --probe
```

After that, Codex can use Agent Reach from any project by calling the CLI:

```powershell
agent-reach collect --channel exa_search --operation search --input "latest AI agent frameworks" --limit 5 --json
agent-reach collect --channel web --operation read --input "https://example.com" --json
agent-reach collect --channel bluesky --operation search --input "OpenAI" --limit 5 --json
agent-reach collect --channel qiita --operation search --input "python user:Qiita" --limit 5 --json
```

This does not require `.codex-plugin`, `.mcp.json`, or `agent_reach/skill` files inside the downstream project.

## Codex Operating Policy

When Codex is working inside an arbitrary project:

- Use the globally installed `agent-reach` CLI by default.
- Do not copy Agent Reach repo files into the project unless the user explicitly asks for repo-local plugin artifacts.
- Use `agent-reach collect --json` as the stable handoff to project code.
- Keep ranking, summarization, scheduling, Discord publishing, and state in the downstream project.
- Treat optional channel failures as partial results unless strict completeness is required.

Large-scale research should use bounded fan-out:

1. Start with 2-4 broad discovery queries at `--limit 5` to `--limit 10`.
2. Dedupe URLs or item IDs in the downstream project.
3. Use specialist channels when the source is known.
4. Deep-read only selected URLs with `web`.
5. Persist raw `CollectionResult` JSON as artifacts in CI when traceability matters.

## GitHub Actions

Use the composite action from this repository:

```yaml
jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - uses: iwachacha/Agent-Reach/.github/actions/setup-agent-reach@main
        with:
          install-twitter-cli: "false"
          install-ytdlp: "false"
          install-mcporter: "false"
      - name: Smoke test Agent Reach
        run: |
          agent-reach version
          agent-reach doctor --json
          agent-reach collect --channel bluesky --operation search --input "OpenAI" --limit 3 --json > agent-reach-results.json
```

Enable optional backends only when the workflow needs them:

```yaml
      - uses: iwachacha/Agent-Reach/.github/actions/setup-agent-reach@main
        with:
          install-twitter-cli: "true"
          install-ytdlp: "true"
          install-mcporter: "true"
          configure-exa: "true"
        env:
          TWITTER_AUTH_TOKEN: ${{ secrets.TWITTER_AUTH_TOKEN }}
          TWITTER_CT0: ${{ secrets.TWITTER_CT0 }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

For reproducible automation, pin `uses:` to a tag or commit instead of `@main`.

## Discord Bot Pattern

For a Discord digest bot such as `ai-news`, keep scheduling, ranking, summarization, dedupe, state, and publishing in the bot project. Use Agent Reach only as the source collection layer.

Recommended collector shape:

```yaml
sources:
  - id: openai_bluesky
    type: agent_reach
    channel: bluesky
    operation: search
    input: OpenAI
    limit: 5
  - id: qiita_llm
    type: agent_reach
    channel: qiita
    operation: search
    input: "LLM user:Qiita"
    limit: 5
```

Recommended subprocess contract:

```python
import json
import subprocess


def collect_with_agent_reach(channel: str, operation: str, value: str, limit: int = 10) -> dict:
    result = subprocess.run(
        [
            "agent-reach",
            "collect",
            "--channel",
            channel,
            "--operation",
            operation,
            "--input",
            value,
            "--limit",
            str(limit),
            "--json",
        ],
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    payload = json.loads(result.stdout or "{}")
    if not payload.get("ok"):
        error = payload.get("error") or {}
        raise RuntimeError(f"agent-reach {channel}/{operation} failed: {error.get('code')}: {error.get('message')}")
    return payload
```

Map `payload["items"]` to the bot's normalized item type:

- `id` -> external item ID
- `title` -> digest title
- `url` -> link target
- `text` -> summary candidate or body snippet
- `author` -> source author
- `published_at` -> item timestamp
- `extras.metrics` / channel-specific extras -> engagement, media, labels, or ranking metadata

Use `agent-reach doctor --json --probe` in CI or scheduled workflows when readiness matters. Treat Twitter/X as optional: `doctor --json` reports authentication state, while `doctor --json --probe` separates live `user` and `search` readiness under `operation_statuses`.
