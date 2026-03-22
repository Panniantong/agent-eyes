# 社交媒体 & 社区

小红书、抖音、Twitter/X、微博、B站、V2EX、Reddit。

## 小红书 / XiaoHongShu

```bash
# 搜索笔记
mcporter call 'xiaohongshu.search_feeds(keyword: "query")'

# 获取笔记详情
mcporter call 'xiaohongshu.get_feed_detail(feed_id: "xxx", xsec_token: "yyy")'

# 获取笔记详情 + 评论
mcporter call 'xiaohongshu.get_feed_detail(feed_id: "xxx", xsec_token: "yyy", load_all_comments: true)'

# 发布内容
mcporter call 'xiaohongshu.publish_content(title: "标题", content: "正文", images: ["/path/img.jpg"], tags: ["tag"])'
```

> **需要登录**: 使用 Cookie-Editor 浏览器插件导出 cookies。运行 `agent-reach doctor` 检查状态。

## 抖音 / Douyin

```bash
# 解析视频信息
mcporter call 'douyin.parse_douyin_video_info(share_link: "https://v.douyin.com/xxx/")'

# 获取无水印下载链接
mcporter call 'douyin.get_douyin_download_link(share_link: "https://v.douyin.com/xxx/")'

# 提取视频文案
mcporter call 'douyin.extract_douyin_text(share_link: "https://v.douyin.com/xxx/")'
```

> **无需登录**

## Twitter/X (xreach CLI)

```bash
# 搜索推文
xreach search "query" -n 10 --json

# 读取单条推文 (支持 /status/ 和 /article/ URL)
xreach tweet URL_OR_ID --json

# 用户时间线
xreach tweets @username -n 20 --json

# 读取完整 thread
xreach thread URL_OR_ID --json
```

> **需要配置**: `agent-reach configure twitter-auth ...` 或通过环境变量配置。
> 如果 fetch 失败，确保安装了 undici: `npm install -g undici`

## 微博 / Weibo

```bash
# 使用 Jina Reader 读取
curl -s "https://r.jina.ai/https://weibo.com/USER_ID/POST_ID"
```

> 微博主要通过网页抓取，推荐使用通用网页读取方式。

## B站 / Bilibili

```bash
# 获取视频元数据
yt-dlp --dump-json "https://www.bilibili.com/video/BVxxx"

# 下载字幕
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --convert-subs vtt --skip-download -o "/tmp/%(id)s" "URL"
```

> **注意**: 服务器 IP 可能遇到 412 错误。使用 `--cookies-from-browser chrome` 或配置代理。

## V2EX (公开 API)

无需认证，直接调用公开 API。

### 热门主题

```bash
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
```

### 节点主题

```bash
# node_name 如: python, tech, jobs, qna, programmers
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" -H "User-Agent: agent-reach/1.0"
```

### 主题详情

```bash
# topic_id 从 URL 获取，如 https://www.v2ex.com/t/1234567
curl -s "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID" -H "User-Agent: agent-reach/1.0"
```

### 主题回复

```bash
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1" -H "User-Agent: agent-reach/1.0"
```

### 用户信息

```bash
curl -s "https://www.v2ex.com/api/members/show.json?username=USERNAME" -H "User-Agent: agent-reach/1.0"
```

### Python 调用示例

```python
from agent_reach.channels.v2ex import V2EXChannel

ch = V2EXChannel()

# 获取热门帖子
topics = ch.get_hot_topics(limit=10)
for t in topics:
    print(f"[{t['node_title']}] {t['title']} ({t['replies']} 回复)")

# 获取节点帖子
node_topics = ch.get_node_topics("python", limit=5)

# 获取帖子详情 + 回复
topic = ch.get_topic(1234567)
print(topic["title"], "—", topic["author"])

# 获取用户信息
user = ch.get_user("Livid")
```

> **节点列表**: https://www.v2ex.com/planes

## Reddit (公开 API)

```bash
# 获取 subreddit 热门帖子
curl -s "https://www.reddit.com/r/SUBREDDIT/hot.json?limit=10" -H "User-Agent: agent-reach/1.0"

# 搜索
curl -s "https://www.reddit.com/search.json?q=QUERY&limit=10" -H "User-Agent: agent-reach/1.0"
```

> **注意**: 服务器 IP 可能遇到 403 错误。搜索建议使用 Exa 代替，或配置代理。
