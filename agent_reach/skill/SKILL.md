---
name: agent-reach
description: >
  Use the internet: search, read, and interact with 16+ platforms including
  Twitter/X, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu (小红书), Douyin (抖音),
  WeChat Articles (微信公众号), LinkedIn, Boss直聘, arXiv, bioRxiv, PubMed,
  RSS, Exa web search, and any web page.
  Use when: (1) user asks to search or read any of these platforms,
  (2) user shares a URL from any supported platform,
  (3) user asks to search the web, find information online, or research a topic,
  (4) user asks to post, comment, or interact on supported platforms,
  (5) user asks to configure or set up a platform channel.
  Triggers: "搜推特", "搜小红书", "看视频", "搜一下", "上网搜", "帮我查", "全网搜索",
  "search twitter", "read tweet", "youtube transcript", "search reddit",
  "read this link", "看这个链接", "B站", "bilibili", "抖音视频",
  "微信文章", "公众号", "LinkedIn", "GitHub issue", "RSS",
  "arXiv", "bioRxiv", "PubMed", "论文", "文献", "preprint",
  "search online", "web search", "find information", "research",
  "帮我配", "configure twitter", "configure proxy", "帮我安装".
---

# Agent Reach — Usage Guide

Upstream tools for 16+ platforms. Call them directly.

Run `agent-reach doctor` to check which channels are available.

## ⚠️ Workspace Rules

**Never create files in the agent workspace.** Use `/tmp/` for temporary output and `~/.agent-reach/` for persistent data.

## Web — Any URL

```bash
curl -s "https://r.jina.ai/URL"
```

## Web Search (Exa)

```bash
mcporter call 'exa.web_search_exa(query: "query", numResults: 5)'
mcporter call 'exa.get_code_context_exa(query: "code question", tokensNum: 3000)'
```

## Twitter/X (xreach)

```bash
xreach search "query" -n 10 --json          # search
xreach tweet URL_OR_ID --json                # read tweet (supports /status/ and /article/ URLs)
xreach tweets @username -n 20 --json         # user timeline
xreach thread URL_OR_ID --json               # full thread
```

## YouTube (yt-dlp)

```bash
yt-dlp --dump-json "URL"                     # video metadata
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"
                                             # download subtitles, then read the .vtt file
yt-dlp --dump-json "ytsearch5:query"         # search
```

## Bilibili (yt-dlp)

```bash
yt-dlp --dump-json "https://www.bilibili.com/video/BVxxx"
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --convert-subs vtt --skip-download -o "/tmp/%(id)s" "URL"
```

> Server IPs may get 412. Use `--cookies-from-browser chrome` or configure proxy.

## Reddit

```bash
curl -s "https://www.reddit.com/r/SUBREDDIT/hot.json?limit=10" -H "User-Agent: agent-reach/1.0"
curl -s "https://www.reddit.com/search.json?q=QUERY&limit=10" -H "User-Agent: agent-reach/1.0"
```

> Server IPs may get 403. Search via Exa instead, or configure proxy.

## GitHub (gh CLI)

```bash
gh search repos "query" --sort stars --limit 10
gh repo view owner/repo
gh search code "query" --language python
gh issue list -R owner/repo --state open
gh issue view 123 -R owner/repo
```

## 小红书 / XiaoHongShu (mcporter)

```bash
mcporter call 'xiaohongshu.search_feeds(keyword: "query")'
mcporter call 'xiaohongshu.get_feed_detail(feed_id: "xxx", xsec_token: "yyy")'
mcporter call 'xiaohongshu.get_feed_detail(feed_id: "xxx", xsec_token: "yyy", load_all_comments: true)'
mcporter call 'xiaohongshu.publish_content(title: "标题", content: "正文", images: ["/path/img.jpg"], tags: ["tag"])'
```

> Requires login. Use Cookie-Editor to import cookies.

## 抖音 / Douyin (mcporter)

```bash
mcporter call 'douyin.parse_douyin_video_info(share_link: "https://v.douyin.com/xxx/")'
mcporter call 'douyin.get_douyin_download_link(share_link: "https://v.douyin.com/xxx/")'
```

> No login needed.

## 微信公众号 / WeChat Articles

**Search** (miku_ai):
```python
python3 -c "
import asyncio
from miku_ai import get_wexin_article
async def s():
    for a in await get_wexin_article('query', 5):
        print(f'{a[\"title\"]} | {a[\"url\"]}')
asyncio.run(s())
"
```

**Read** (Camoufox — bypasses WeChat anti-bot):
```bash
cd ~/.agent-reach/tools/wechat-article-for-ai && python3 main.py "https://mp.weixin.qq.com/s/ARTICLE_ID"
```

> WeChat articles cannot be read with Jina Reader or curl. Must use Camoufox.

## LinkedIn (mcporter)

```bash
mcporter call 'linkedin.get_person_profile(linkedin_url: "https://linkedin.com/in/username")'
mcporter call 'linkedin.search_people(keyword: "AI engineer", limit: 10)'
```

Fallback: `curl -s "https://r.jina.ai/https://linkedin.com/in/username"`

## Boss直聘 (mcporter)

```bash
mcporter call 'bosszhipin.get_recommend_jobs_tool(page: 1)'
mcporter call 'bosszhipin.search_jobs_tool(keyword: "Python", city: "北京")'
```

Fallback: `curl -s "https://r.jina.ai/https://www.zhipin.com/job_detail/xxx"`

## RSS

```python
python3 -c "
import feedparser
for e in feedparser.parse('FEED_URL').entries[:5]:
    print(f'{e.title} — {e.link}')
"
```

## arXiv (Academic Preprints)

```bash
# Search papers
curl -s "http://export.arxiv.org/api/query?search_query=all:virtual+cell&max_results=5" | python3 -c "
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.stdin).getroot()
ns = {'a': 'http://www.w3.org/2005/Atom'}
for e in root.findall('a:entry', ns):
    title = e.find('a:title', ns).text.strip().replace(chr(10), ' ')
    url = e.find('a:id', ns).text
    print(f'{title}')
    print(f'  {url}')
    print()
"

# Get paper by arXiv ID
curl -s "http://export.arxiv.org/api/query?id_list=2410.05390"

# Read full paper page (via Jina Reader)
curl -s "https://r.jina.ai/https://arxiv.org/abs/2410.05390"
```

> Free, no API key needed. Rate limit: ~3 requests/second.

## bioRxiv / medRxiv (Biology & Medical Preprints)

```bash
# Search recent papers by date range (format: YYYY-MM-DD/YYYY-MM-DD/cursor/page_size)
curl -s "https://api.biorxiv.org/details/biorxiv/2026-02-01/2026-03-06/0/5" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('collection', []):
    print(p['title'])
    print(f'  https://doi.org/{p[\"doi\"]}')
    print()
"

# Also works for medRxiv
curl -s "https://api.biorxiv.org/details/medrxiv/2026-02-01/2026-03-06/0/5"

# Read full paper (via Jina Reader)
curl -s "https://r.jina.ai/https://www.biorxiv.org/content/10.1101/xxx"
```

> Free, no API key needed.

## PubMed (Biomedical Literature)

```bash
# Search articles (returns PMIDs)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CRC+drug+resistance&retmax=5&retmode=json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
ids = data['esearchresult']['idlist']
print(f'Found {data[\"esearchresult\"][\"count\"]} results')
for pmid in ids:
    print(f'  https://pubmed.ncbi.nlm.nih.gov/{pmid}/')
"

# Fetch abstracts by PMID
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=39112345,39112346&retmode=xml" | python3 -c "
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.stdin).getroot()
for art in root.findall('.//PubmedArticle'):
    title = art.find('.//ArticleTitle')
    abstract = art.find('.//AbstractText')
    pmid = art.find('.//PMID')
    if title is not None: print(f'[PMID {pmid.text}] {title.text}')
    if abstract is not None: print(f'  {abstract.text[:300]}...')
    print()
"

# Read full article page (via Jina Reader)
curl -s "https://r.jina.ai/https://pubmed.ncbi.nlm.nih.gov/PMID/"
```

> Free, no API key needed. Rate limit: 3/sec (10/sec with free NCBI API key).
> Get API key: https://www.ncbi.nlm.nih.gov/account/settings/

## Troubleshooting

- **Channel not working?** Run `agent-reach doctor` — shows status and fix instructions.
- **Twitter fetch failed?** Ensure `undici` is installed: `npm install -g undici`. Configure proxy: `agent-reach configure proxy URL`.

## Setting Up a Channel ("帮我配 XXX")

If a channel needs setup (cookies, Docker, etc.), fetch the install guide:
https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md

User only provides cookies. Everything else is your job.
