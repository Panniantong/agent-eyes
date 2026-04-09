# Web And RSS

Use Jina Reader for readable markdown from normal pages.

```powershell
agent-reach collect --channel web --operation read --input "https://example.com" --json
```

Use RSS feeds when the source exposes one:

```powershell
agent-reach collect --channel rss --operation read --input "https://example.com/feed.xml" --limit 3 --json
```

Prefer `web` over bespoke scraping for documentation, release notes, blog posts, note, Qiita, and Zenn.
