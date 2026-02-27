# Changelog / 更新日志

All notable changes to this project will be documented in this file.

本项目的所有重要变更都会记录在此文件中。

---

## [1.3.0] - 2026-02-27

### 📈 Improvements / 改进

- Added quality gates: `ruff` + `mypy` + `pytest` in CI
- CI test matrix now covers Python `3.10/3.11/3.12`
- `doctor` now reports four health signals: `installed/configured/reachable/authenticated`
- Added local-only telemetry (`~/.agent-reach/telemetry.jsonl`, opt-out via `AGENT_REACH_TELEMETRY=0`)
- Added reproducible dependency strategy (`constraints.txt` + dependency locking guide)
- Added channel contract tests and telemetry tests for regression coverage
- 新增质量门禁：CI 同时执行 `ruff`、`mypy`、`pytest`
- CI Python 版本矩阵扩展为 `3.10/3.11/3.12`
- `doctor` 新增四级健康信号：`installed/configured/reachable/authenticated`
- 新增本地遥测（仅本机写入，可通过 `AGENT_REACH_TELEMETRY=0` 关闭）
- 新增依赖可复现方案（`constraints.txt` 与依赖锁定文档）
- 新增渠道契约测试与 telemetry 测试，提升回归可靠性

---

## [1.2.0] - 2026-02-27

### 📈 Improvements / 改进

- CLI command model clarified and unified around: `install`, `setup`, `configure`, `doctor`, `watch`, `check-update`, `version`
- Removed stale command wording from docs (`read/search-*` examples were from older iterations)
- Added CI regression workflow for `pytest`
- 明确并统一当前 CLI 命令模型：`install`、`setup`、`configure`、`doctor`、`watch`、`check-update`、`version`
- 清理文档中的历史命令表述（`read/search-*` 旧示例）
- 新增 `pytest` 持续集成回归流程

---

## [1.1.0] - 2025-02-25

### 🆕 New Channels / 新增渠道

#### ~~📷 Instagram~~ (removed — upstream blocked)
- ~~Read public posts and profiles via [instaloader](https://github.com/instaloader/instaloader)~~
- **Removed:** Instagram's aggressive anti-scraping measures broke all available open-source tools (instaloader, etc.). See [instaloader#2585](https://github.com/instaloader/instaloader/issues/2585). Will re-add when upstream recovers.
- **已移除：** Instagram 反爬封杀导致所有开源工具（instaloader 等）失效。上游恢复后会重新加回。

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
- CLI: expanded channel compatibility checks for LinkedIn and Boss直聘
- Updated install guide with setup instructions for new channels
- 渠道数量：9 → 12
- `agent-reach doctor` 现在检测全部 12 个渠道
- CLI：增强 LinkedIn、Boss直聘 渠道兼容性检测
- 安装指南新增渠道配置说明

---

## [1.0.0] - 2025-02-24

### 🎉 Initial Release / 首次发布

- 9 channels: Web, Twitter/X, YouTube, Bilibili, GitHub, Reddit, XiaoHongShu, RSS, Exa Search
- CLI with install/configure/doctor workflows (scaffold-style setup)
- Unified channel interface — each platform is a single pluggable Python file
- Auto-detection of local vs server environments
- Built-in diagnostics via `agent-reach doctor`
- Skill registration for Claude Code / OpenClaw / Cursor
- 9 个渠道：网页、Twitter/X、YouTube、B站、GitHub、Reddit、小红书、RSS、Exa 搜索
- CLI 采用脚手架式工作流（install/configure/doctor）
- 统一渠道接口 — 每个平台一个独立可插拔的 Python 文件
- 自动检测本地/服务器环境
- 内置诊断 `agent-reach doctor`
- Skill 注册支持 Claude Code / OpenClaw / Cursor
