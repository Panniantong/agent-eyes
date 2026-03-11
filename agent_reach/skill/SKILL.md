---
name: agent-reach
description: >
  Give your AI agent eyes to see the entire internet. 7500+ GitHub stars.
  Search and read 15 platforms: Twitter/X, Reddit, YouTube, GitHub, Bilibili,
  XiaoHongShu (小红书), Douyin (抖音), Weibo (微博), WeChat Articles (微信公众号),
  LinkedIn, Instagram, V2EX, RSS, Exa web search, and any web page.
  One command install, zero config for 8 channels, agent-reach doctor for diagnostics.
  Use when: (1) user asks to search or read any of these platforms,
  (2) user shares a URL from any supported platform,
  (3) user asks to search the web, find information online, or research a topic,
  (4) user asks to post, comment, or interact on supported platforms,
  (5) user asks to configure or set up a platform channel.
  Triggers: "搜推特", "搜小红书", "看视频", "搜一下", "上网搜", "帮我查", "全网搜索",
  "search twitter", "read tweet", "youtube transcript", "search reddit",
  "read this link", "看这个链接", "B站", "bilibili", "抖音视频",
  "微信文章", "公众号", "LinkedIn", "GitHub issue", "RSS", "微博",
  "V2EX", "v2ex", "节点", "看主题", "技术社区",
  "search online", "web search", "find information", "research",
  "帮我配", "configure twitter", "configure proxy", "帮我安装".
metadata:
  openclaw:
    homepage: https://github.com/Panniantong/Agent-Reach
---

# Agent Reach — Usage Guide

Upstream tools for 13+ platforms. Call them directly.

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

## V2EX (public API)

```bash
# 热门主题
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"

# 节点主题（node_name 如 python、tech、jobs、qna）
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" -H "User-Agent: agent-reach/1.0"

# 主题详情（topic_id 从 URL 获取，如 https://www.v2ex.com/t/1234567）
curl -s "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID" -H "User-Agent: agent-reach/1.0"

# 主题回复
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1" -H "User-Agent: agent-reach/1.0"

# 用户信息
curl -s "https://www.v2ex.com/api/members/show.json?username=USERNAME" -H "User-Agent: agent-reach/1.0"
```

Python 调用示例（V2EXChannel）：

```python
from agent_reach.channels.v2ex import V2EXChannel

ch = V2EXChannel()

# 获取热门帖子（默认 20 条）
# 返回字段：id, title, url, replies, node_name, node_title, content(前200字), created
topics = ch.get_hot_topics(limit=10)
for t in topics:
    print(f"[{t['node_title']}] {t['title']} ({t['replies']} 回复) {t['url']}")
    print(f"  id={t['id']} created={t['created']}")

# 获取指定节点的最新帖子
# 返回字段：id, title, url, replies, node_name, node_title, content(前200字), created
node_topics = ch.get_node_topics("python", limit=5)
for t in node_topics:
    print(t["id"], t["title"], t["url"])

# 获取单个帖子详情 + 回复列表
# 返回字段：id, title, url, content, replies_count, node_name, node_title,
#           author, created, replies (list of {author, content, created})
topic = ch.get_topic(1234567)
print(topic["title"], "—", topic["author"])
for r in topic["replies"]:
    print(f"  {r['author']}: {r['content'][:80]}")

# 获取用户信息
# 返回字段：id, username, url, website, twitter, psn, github, btc, location, bio, avatar, created
user = ch.get_user("Livid")
print(user["username"], user["bio"], user["github"])

# 搜索（V2EX 公开 API 不支持，会返回说明信息）
result = ch.search("asyncio")
print(result[0]["error"])  # 提示使用站内搜索或 Exa channel
```

> No auth required. Results are public JSON. V2EX 节点名见 https://www.v2ex.com/planes

## RSS (feedparser)

## RSS

```python
python3 -c "
import feedparser
for e in feedparser.parse('FEED_URL').entries[:5]:
    print(f'{e.title} — {e.link}')
"
```

## Troubleshooting

- **Channel not working?** Run `agent-reach doctor` — shows status and fix instructions.
- **Twitter fetch failed?** Ensure `undici` is installed: `npm install -g undici`. Configure proxy: `agent-reach configure proxy URL`.

## Setting Up a Channel ("帮我配 XXX")

If a channel needs setup (cookies, Docker, etc.), fetch the install guide:
https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md

User only provides cookies. Everything else is your job.
