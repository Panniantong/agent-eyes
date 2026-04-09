# Agent Reach Python SDK

`AgentReachClient` is the first-class external API for Python projects.

## Install

```powershell
uv tool install .
```

Or from a checkout used directly by another Python project:

```powershell
uv pip install -e .
```

## Basic usage

```python
from agent_reach import AgentReachClient

client = AgentReachClient()

github_repo = client.github.read("openai/openai-python")
web_page = client.web.read("https://example.com")
search_results = client.exa.search("latest gpt-5.4 release notes", limit=3)
```

## Result shape

Every collection call returns the same envelope:

- `ok`
- `channel`
- `operation`
- `items`
- `raw`
- `meta`
- `error`

Each entry in `items` uses the same normalized shape:

- `id`
- `kind`
- `title`
- `url`
- `text`
- `author`
- `published_at`
- `source`
- `extras`

Use `items` for downstream automation and `raw` when you need backend-native details.

## Discord bot style usage

```python
from agent_reach import AgentReachClient

client = AgentReachClient()

def collect_digest():
    results = []
    results.append(client.exa.search("OpenAI pricing", limit=3))
    results.append(client.github.read("openai/openai-python"))
    results.append(client.rss.read("https://hnrss.org/frontpage", limit=3))

    messages = []
    for result in results:
        if not result["ok"]:
            messages.append(f"[{result['channel']}] {result['error']['message']}")
            continue
        for item in result["items"]:
            messages.append(f"{item['source']}: {item['title']} {item['url']}")
    return messages
```

## Non-interactive behavior

- collection never prompts interactively
- config values and environment variables are both supported
- failures still return the same JSON-compatible envelope

Useful environment variables:

- `GITHUB_TOKEN`
- `TWITTER_AUTH_TOKEN`
- `TWITTER_CT0`
