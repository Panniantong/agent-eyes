# Changelog / 更新日志

All notable changes to this project will be documented in this file.

本项目的所有重要变更都会记录在此文件中。

---

## [1.1.0] - 2025-02-25

### 🆕 New Channels / 新增渠道

#### 📷 Instagram
- Read public posts and profiles via [instaloader](https://github.com/instaloader/instaloader)
- Search via Exa (free, no API key)
- Optional cookie login for private content
- 通过 instaloader 读取公开帖子和 Profile
- 搜索通过 Exa（免费，无需 API Key）
- 可选 Cookie 登录解锁私密内容

#### 💼 LinkedIn
- Read person profiles, company pages, and job details via [linkedin-scraper-mcp](https://github.com/stickerdaniel/linkedin-mcp-server)
- Search people and jobs via MCP, with Exa fallback
- Fallback to Jina Reader when MCP is not configured
- 通过 linkedin-scraper-mcp 读取个人 Profile、公司页面、职位详情
- 通过 MCP 搜索人才和职位，Exa 兜底
- 未配置 MCP 时自动 fallback 到 Jina Reader

#### 🏢 Boss直聘
- QR code login via [mcp-bosszp](https://github.com/mucsbr/mcp-bosszp)
- Job search and recruiter greeting via MCP
- Fallback to Jina Reader for reading job pages
- 通过 mcp-bosszp 扫码登录
- MCP 搜索职位、向 HR 打招呼
- Jina Reader 兜底读取职位页面

### 📈 Improvements / 改进

- Channel count: 9 → 12
- `agent-reach doctor` now detects all 12 channels
- CLI: added `search-instagram`, `search-linkedin`, `search-bosszhipin` subcommands
- Updated install guide with setup instructions for new channels
- 渠道数量：9 → 12
- `agent-reach doctor` 现在检测全部 12 个渠道
- CLI：新增 `search-instagram`、`search-linkedin`、`search-bosszhipin` 子命令
- 安装指南新增三个渠道的配置说明

---

## [1.0.0] - 2025-02-24

### 🎉 Initial Release / 首次发布

- 9 channels: Web, Twitter/X, YouTube, Bilibili, GitHub, Reddit, XiaoHongShu, RSS, Exa Search
- CLI with `read`, `search`, `doctor`, `install` commands
- Unified channel interface — each platform is a single pluggable Python file
- Auto-detection of local vs server environments
- Built-in diagnostics via `agent-reach doctor`
- Skill registration for Claude Code / OpenClaw / Cursor
- 9 个渠道：网页、Twitter/X、YouTube、B站、GitHub、Reddit、小红书、RSS、Exa 搜索
- CLI 支持 `read`、`search`、`doctor`、`install` 命令
- 统一渠道接口 — 每个平台一个独立可插拔的 Python 文件
- 自动检测本地/服务器环境
- 内置诊断 `agent-reach doctor`
- Skill 注册支持 Claude Code / OpenClaw / Cursor
