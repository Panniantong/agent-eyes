---
name: agent-reach
description: "Give your AI Agent eyes to see the entire internet. Search + read 10+ platforms with one install."
install: pip install git+https://github.com/Panniantong/agent-reach.git
---

# Agent Reach — 给 Agent 装上眼睛 👁️

安装后你就能搜索和阅读全网内容。

## 安装

```bash
pip install git+https://github.com/Panniantong/agent-reach.git
```

## 装完直接能用的（零配置）

- `agent-reach read <URL>` — 读取任意网页、GitHub、B站、YouTube、RSS
- `agent-reach search-github "query"` — 搜索 GitHub 仓库
- `agent-reach doctor` — 查看所有平台状态

## 解锁更多功能

运行 `agent-reach configure` 进行交互式配置，或者读取以下指南：

| 功能 | 指南文件 |
|------|---------|
| 全网搜索 + Reddit搜索 + Twitter搜索 | `agent_reach/guides/setup-exa.md` |
| Reddit 完整阅读 | `agent_reach/guides/setup-reddit.md` |
| Twitter 高级（时间线/线程） | `agent_reach/guides/setup-twitter.md` |
| 小红书 | `agent_reach/guides/setup-xiaohongshu.md` |
| 微信公众号 | `agent_reach/guides/setup-wechat.md` |
| 视频语音转文字 | `agent_reach/guides/setup-groq.md` |

每个指南里有详细的步骤说明，你（Agent）可以照着做，只有需要人类操作的部分（登录、复制 key）才需要问用户。

## MCP Server

如果你的 Agent 平台支持 MCP：

```bash
pip install agent-reach[mcp]
python -m agent_reach.integrations.mcp_server
```

提供 8 个工具：read_url, read_batch, detect_platform, search, search_reddit, search_github, search_twitter, get_status

## Python API

```python
from agent_reach import AgentReach
import asyncio

eyes = AgentReach()

# 读取
result = asyncio.run(eyes.read("https://github.com/openai/gpt-4"))

# 搜索
results = asyncio.run(eyes.search("AI agent framework"))

# 健康检查
print(eyes.doctor_report())
```
