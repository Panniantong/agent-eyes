<h1 align="center">👁️ Agent Reach</h1>

<p align="center">
  <strong>给你的 AI Agent 一键装上互联网能力</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+"></a>
  <a href="https://github.com/Panniantong/agent-reach/stargazers"><img src="https://img.shields.io/github/stars/Panniantong/agent-reach?style=for-the-badge" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#30-秒上手">快速开始</a> · <a href="docs/README_en.md">English</a> · <a href="#支持的平台">支持平台</a> · <a href="#设计理念">设计理念</a>
</p>

---

## 为什么需要 Agent Reach？

AI Agent 已经能访问互联网——但只是"能上网"而已。

真正有价值的信息，散落在各种社媒和私域平台里：Twitter 上的行业讨论、Reddit 上的真实反馈、YouTube 的深度教程、小红书上的用户口碑、B站的技术视频、GitHub 的开源动态……**这些地方才是信息密度最高的地方**，但每个平台都有自己的门槛：

| 痛点 | 现状 |
|------|------|
| Twitter API | $100/月起步 |
| Reddit | 服务器 IP 直接 403 |
| 小红书 | 必须登录才能看 |
| B站 | 屏蔽海外/服务器 IP |

你要让 Agent 接入这些平台，就得一个一个去踩坑、装工具、调配置。

**Agent Reach 把这件事变成一行命令：**

```
帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

复制给你的 Agent，30 秒后它就能读推特、搜 Reddit、看 B站了。

### ✅ 在你用之前，你可能想知道

| | |
|---|---|
| 💰 **完全免费** | 所有工具开源、所有 API 免费。唯一可能花钱的是服务器代理（$1/月），本地电脑不需要 |
| 🔒 **隐私安全** | Cookie 只存在你本地，不上传不外传。代码完全开源，随时可审查 |
| 🔄 **持续更新** | 底层工具（yt-dlp、birdx、Jina Reader 等）定期追踪更新到最新版，你不用自己盯 |
| 🤖 **兼容所有 Agent** | Claude Code、OpenClaw、Cursor、Windsurf……任何能跑命令行的 Agent 都能用 |
| 🩺 **自带诊断** | `agent-reach doctor` 一条命令告诉你哪个通、哪个不通、怎么修 |

---

## 支持的平台

| 平台 | 能力 | 配置难度 | 说明 |
|------|------|:--------:|------|
| 🌐 **网页** | 阅读 | 零配置 | 任意 URL → 干净 Markdown（[Jina Reader](https://github.com/jina-ai/reader) ⭐9.8K 驱动） |
| 🐦 **Twitter/X** | 阅读 · 搜索 | 零配置 / Cookie | 单条推文零配置可读。配置 Cookie 可解锁搜索、时间线、发推（[birdx](https://github.com/runesleo/birdx) 驱动） |
| 📕 **小红书** | 阅读 · 搜索 · **发帖 · 评论 · 点赞** | mcporter | 通过 [xiaohongshu-mcp](https://github.com/user/xiaohongshu-mcp) 内部 API，安装即可用 |
| 🔍 **全网搜索** | 搜索 | 自动配置 | 安装时自动配置，免 Key 免费用（[Exa](https://exa.ai) via [mcporter](https://github.com/nicepkg/mcporter) 驱动） |
| 📦 **GitHub** | 阅读 · 搜索 | 零配置 | [gh CLI](https://cli.github.com) 驱动，公开仓库直接可用。`gh auth login` 后可解锁 Fork、Issue、PR |
| 📺 **YouTube** | 阅读 · **搜索** | 零配置 | 视频字幕 + 搜索，支持 1800+ 视频网站（[yt-dlp](https://github.com/yt-dlp/yt-dlp) ⭐148K 驱动） |
| 📺 **B站** | 阅读 · **搜索** | 零配置 / 代理 | 视频信息 + 字幕 + 搜索。本地直接用，服务器配个代理（[yt-dlp](https://github.com/yt-dlp/yt-dlp) 驱动） |
| 📡 **RSS** | 阅读 | 零配置 | 任意 RSS/Atom 源（[feedparser](https://github.com/kurtmckee/feedparser) ⭐2.3K 驱动） |
| 📖 **Reddit** | 搜索 · 阅读 | 免费 / 代理 | 搜索通过 Exa 免费直接可用。读帖子配个代理即可 |

> **配置难度说明：** 零配置 = 装好即用 · 自动配置 = 安装时搞定 · mcporter = 需要 MCP 服务 · Cookie = 从浏览器导出 · 代理 = $1/月

---

## 30 秒上手

复制给你的 AI Agent（Claude Code、OpenClaw、Cursor 等）：

```
帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

Agent 自动安装、检测环境、告诉你哪些功能已经可以用。

<details>
<summary>手动安装</summary>

```bash
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```
</details>

---

## 装好就能用

不需要任何配置，告诉 Agent 就行：

- "帮我看看这个链接" → 任意网页
- "这个 GitHub 仓库是做什么的" → GitHub 仓库、Issue、代码
- "这个视频讲了什么" → YouTube / B站字幕提取
- "帮我看看这条推文" → Twitter 推文
- "订阅这个 RSS" → RSS / Atom 源
- "搜一下 GitHub 上有什么 LLM 框架" → GitHub 搜索

**不需要记命令。** Agent 自己知道该调什么。

---

## 按需解锁

不用的不用配。每一步都可以跳过，直接告诉 Agent 就行。

### 🍪 Cookie — 免费，2 分钟

告诉 Agent "帮我配置 Twitter Cookie"，Agent 会引导你从浏览器导入。本地电脑可以一键自动导入。

### 🌐 代理 — $1/月，仅服务器需要

Reddit 和 B站封服务器 IP。买个代理（推荐 [Webshare](https://webshare.io)，$1/月），把地址发给 Agent 就行。

> 本地电脑不需要代理。Reddit 搜索通过 Exa 免费可用，不买代理也能搜。

---

## 状态一目了然

```
$ agent-reach doctor

👁️  Agent Reach 状态
========================================

✅ 装好即用：
  ✅ GitHub 仓库和代码 — 公开仓库可读可搜。配置 gh CLI 或 Token 可解锁 Fork、Issue、PR 等操作
  ✅ Twitter/X 推文 — 可读取推文。配置 Cookie 可解锁搜索和发推
  ✅ YouTube 视频字幕 — yt-dlp
  ⚠️  B站视频信息和字幕 — 服务器 IP 可能被封，配置代理即可解决
  ✅ RSS/Atom 订阅源 — feedparser
  ✅ 网页（任意 URL） — Jina Reader API

🔍 搜索（免费 Exa Key 即可解锁）：
  ⬜ 全网语义搜索 — 注册 exa.ai 获取免费 Key，配置一下就能用

🔧 配置后可用：
  ⬜ Reddit 帖子和评论 — 搜索用 Exa 免费可用。读帖子需配个代理
  ⬜ 小红书笔记 — 需要配置 Cookie。导入浏览器 Cookie 即可

状态：6/9 个渠道可用
```

---

## 设计理念

**Agent Reach 是一个 Agent 初始化脚手架，不是框架。**

你给一个新 Agent 装环境的时候，总要花时间去找工具、装依赖、调配置——Twitter 用什么读？Reddit 怎么绕封？YouTube 字幕怎么提取？每次都要重新踩一遍。

Agent Reach 做的事情很简单：**帮你把这些选型和配置的活儿做完了。**

| 场景 | 选型 | 为什么选它 |
|------|------|-----------|
| 读网页 | [Jina Reader](https://github.com/jina-ai/reader) | 9.8K Star，免费，不需要 API Key |
| 读推特 | [birdx](https://github.com/runesleo/birdx) | Cookie 登录，不用花 $100/月买官方 API |
| 视频字幕 + 搜索 | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 148K Star，YouTube + B站 + 1800 站通吃 |
| 搜全网 | [Exa](https://exa.ai) via [mcporter](https://github.com/nicepkg/mcporter) | AI 语义搜索，MCP 接入免 Key |
| GitHub | [gh CLI](https://cli.github.com) | 官方工具，认证后完整 API 能力 |
| 读 RSS | [feedparser](https://github.com/kurtmckee/feedparser) | Python 生态标准选择，2.3K Star |
| 小红书 | [xiaohongshu-mcp](https://github.com/user/xiaohongshu-mcp) | 内部 API，不受反爬限制 |

每个平台一个文件，每个文件 ~50 行代码。后端工具随时可以换——哪天出了更好的工具，改一个文件就行，其他不用动。

<details>
<summary>项目结构</summary>

```
agent_reach/channels/
├── web.py          → Jina Reader
├── twitter.py      → birdx
├── youtube.py      → yt-dlp
├── github.py       → GitHub API
├── bilibili.py     → Bilibili API
├── reddit.py       → Reddit JSON API
├── xiaohongshu.py  → XHS Web API
├── rss.py          → feedparser
└── exa_search.py   → Exa Search API
```
</details>

---

## 贡献

欢迎提 [Issue](https://github.com/Panniantong/agent-reach/issues) 和 [PR](https://github.com/Panniantong/agent-reach/pulls)。

想加新平台？复制任意一个 channel 文件，改改就行——每个文件只有 ~50 行。

## 致谢

[Jina Reader](https://github.com/jina-ai/reader) · [yt-dlp](https://github.com/yt-dlp/yt-dlp) · [birdx](https://github.com/runesleo/birdx) · [Exa](https://exa.ai) · [feedparser](https://github.com/kurtmckee/feedparser)

## License

[MIT](LICENSE)
