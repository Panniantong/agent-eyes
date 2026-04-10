# Web And RSS

Use Jina Reader for readable markdown from normal pages.

```powershell
agent-reach collect --channel web --operation read --input "https://example.com" --json
```

Use RSS feeds when the source exposes one:

```powershell
agent-reach collect --channel rss --operation read --input "https://example.com/feed.xml" --limit 3 --json
```

Prefer `web` over bespoke scraping for documentation, release notes, blog posts, note, Zenn, and other generic sites. Use the dedicated `qiita` channel when you need direct Qiita search.

Use Crawl4AI only when the caller needs browser-backed extraction and the optional dependency plus browser runtime are installed:

```powershell
uv pip install "agent-reach[crawl4ai] @ git+https://github.com/iwachacha/Agent-Reach.git"
python -m playwright install chromium
agent-reach collect --channel crawl4ai --operation read --input "https://example.com" --json
agent-reach collect --channel crawl4ai --operation crawl --input "https://example.com" --query "pricing and faq" --limit 10 --json
```

`crawl4ai crawl` is same-origin bounded and requires the external caller to provide the crawl goal with `--query`.
