# 👁️ Agent Eyes

**让你的 AI Agent 看见整个互联网。**

Agent Eyes 是一个开源的粘合剂项目。它把互联网上最强的几个开源工具整合到一起，让你的 Agent 一次安装就获得所有能力。

> 我们不重复造轮子。我们找到每个领域最好的轮子，然后把它们装到你的 Agent 上。

[English](docs/README_en.md)

---

## 我们整合了什么

每个平台背后都是一个久经考验的开源项目。Agent Eyes 只是把它们粘在一起，让你一行命令就能全部用上。

### 🌐 Jina Reader — 把任意网页变成干净文本

[Jina Reader](https://github.com/jina-ai/reader)（⭐ 9.8K）能把任意 URL 转成 LLM 友好的 Markdown。不是简单的爬虫——它能处理 JavaScript 渲染的页面、去掉广告和导航栏、只留下正文内容。Agent Eyes 用它来读取所有网页。

```bash
agent-eyes read "https://任意网页"
```

### 📺 yt-dlp — 从 1800+ 个视频网站提取字幕

[yt-dlp](https://github.com/yt-dlp/yt-dlp)（⭐ 148K）是互联网上最强的视频下载工具，支持 **1800+ 个视频网站**——不只是 YouTube，还有 B站、Twitch、TikTok 等等。Agent Eyes 用它来提取视频字幕，让 Agent 能"看"视频内容。

```bash
agent-eyes read "https://www.youtube.com/watch?v=xxx"
agent-eyes read "https://www.bilibili.com/video/BVxxx"
```

### 🔍 Exa — AI 原生的语义搜索引擎

[Exa](https://exa.ai) 不是传统的关键词搜索——它用神经网络理解你搜索的**语义**，找到真正相关的内容。一个免费 Key（1000 次/月），同时解锁全网搜索、Reddit 搜索和 Twitter 搜索。

```bash
agent-eyes search "2025年最适合个人开发者的 AI 工具"
agent-eyes search-reddit "best self-hosted LLM" --sub LocalLLaMA
agent-eyes search-twitter "AI agent 实战"
```

### 🐦 birdx — 无需 API，用 Cookie 玩转 Twitter

[birdx](https://github.com/runesleo/birdx) 让你不需要 Twitter API Key（那个贵得离谱），只要浏览器 Cookie 就能搜索时间线、读完整线程、浏览任何用户的推文。

```bash
agent-eyes read "https://x.com/elonmusk/status/xxx"     # 读推文
agent-eyes search-twitter "Claude Code tips"               # 搜推特
```

### 📡 feedparser — 万能 RSS 阅读器

[feedparser](https://github.com/kurtmckee/feedparser)（⭐ 2.3K）是 Python 世界的 RSS/Atom 解析标准，能处理几乎任何格式的订阅源。

```bash
agent-eyes read "https://hnrss.org/frontpage"              # Hacker News
agent-eyes read "https://rsshub.app/github/trending/daily"  # GitHub Trending
```

### 📺 Bilibili API — B站视频信息 + 字幕

直接调用 B站公开 API，提取视频标题、描述、字幕。本地电脑直接可用，服务器需要代理。

### 📕 小红书 — Cookie 一配就能读

配好 Cookie 后可以读取小红书笔记的完整内容和评论。

---

## 30 秒上手

把这句话复制给你的 AI Agent：

```
帮我安装 Agent Eyes：https://raw.githubusercontent.com/Panniantong/agent-eyes/main/docs/install.md
```

> 💡 打开你的 Agent 对话框（Claude Code 终端、OpenClaw 聊天、Cursor Chat），直接粘贴就行。

Agent 会自动装好，告诉你哪些功能已经可以用。

<details>
<summary>手动安装</summary>

```bash
pip install https://github.com/Panniantong/agent-eyes/archive/main.zip
agent-eyes install --env=auto
agent-eyes doctor
```
</details>

---

## 解锁更多

### 🔍 搜索（免费，30 秒）

注册 [Exa](https://exa.ai) 拿一个免费 Key：

```bash
agent-eyes configure exa-key 你的KEY
```

### 🍪 Cookie 解锁（免费，2 分钟）

本地电脑一键导入所有平台 cookies：

```bash
agent-eyes configure --from-browser chrome
```

服务器用户？装个 [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) 扩展，点 Export → Header String，粘贴给 Agent。

### 🌐 代理（$1/月，仅服务器）

Reddit 和 B站封服务器 IP。推荐 [Webshare](https://webshare.io)，一个代理管两个平台：

```bash
agent-eyes configure proxy http://用户名:密码@IP:端口
```

> 不买也行——Reddit 搜索通过 Exa 免费可用。

---

## 三种接入方式

**命令行** · **Python API** · **MCP Server**

```bash
agent-eyes read "URL"              # 阅读
agent-eyes search "关键词"          # 搜索
agent-eyes doctor                   # 状态检查
```

```python
from agent_eyes import AgentEyes
eyes = AgentEyes()
result = asyncio.run(eyes.read("https://example.com"))
```

<details>
<summary>MCP Server 配置</summary>

```bash
pip install agent-eyes[mcp]
```

```json
{
  "mcpServers": {
    "agent-eyes": {
      "command": "python",
      "args": ["-m", "agent_eyes.integrations.mcp_server"]
    }
  }
}
```
</details>

---

## 配置速查

| 命令 | 作用 |
|------|------|
| `agent-eyes doctor` | 查看状态 |
| `agent-eyes configure --from-browser chrome` | 一键导入 cookies |
| `agent-eyes configure exa-key KEY` | 解锁搜索 |
| `agent-eyes configure twitter-cookies "..."` | 解锁 Twitter 高级 |
| `agent-eyes configure xhs-cookie "..."` | 解锁小红书 |
| `agent-eyes configure proxy URL` | 解锁 Reddit + B站（服务器）|

---

## 设计理念

Agent Eyes 不造轮子，只做胶水：

- 每个频道 ~50 行代码，就是对底层工具的薄封装
- 换后端？改一个文件就行
- 99% 功能免费，剩下 1% 也就 $1/月
- 支持 CLI、MCP Server、Python API 三种接入

<details>
<summary>架构</summary>

```
┌──────────────────────────────────────────┐
│           Agent Eyes（胶水层）              │
│                                           │
│  web.py      → Jina Reader (⭐ 9.8K)      │
│  youtube.py  → yt-dlp (⭐ 148K)           │
│  twitter.py  → birdx                      │
│  exa.py      → Exa Search                 │
│  github.py   → GitHub API                 │
│  bilibili.py → Bilibili API               │
│  reddit.py   → Reddit JSON API            │
│  rss.py      → feedparser (⭐ 2.3K)       │
│  xhs.py      → XHS Web API                │
│                                           │
│  CLI · MCP Server · Python API             │
└──────────────────────────────────────────┘
```
</details>

---

## 致谢

感谢这些项目，Agent Eyes 站在它们的肩膀上：

- [Jina Reader](https://github.com/jina-ai/reader) — 网页转 Markdown
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 1800+ 视频网站字幕提取
- [birdx](https://github.com/runesleo/birdx) — 无 API Key 的 Twitter 访问
- [Exa](https://exa.ai) — 语义搜索引擎
- [feedparser](https://github.com/kurtmckee/feedparser) — RSS/Atom 解析

## License

MIT
