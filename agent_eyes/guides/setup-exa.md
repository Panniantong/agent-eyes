# Exa Search 配置指南

## 功能说明
Exa 是一个语义搜索引擎，免费提供 1000 次/月搜索。配置后解锁：
- 全网搜索
- Reddit 搜索（通过 site:reddit.com）
- Twitter 搜索（通过 site:x.com）

## Agent 可自动完成的步骤

1. 检查是否已配置：
```bash
agent-eyes doctor | grep "Web Search"
```

2. 如果用户提供了 key，写入配置：
```bash
# 方法1: 通过 setup 命令
agent-eyes setup

# 方法2: 直接写入配置文件
python3 -c "
from agent_eyes.config import Config
c = Config()
c.set('exa_api_key', '用户提供的KEY')
print('✅ Exa API key saved')
"
```

3. 测试是否有效：
```bash
agent-eyes search "test query" -n 1
```

## 需要用户手动做的步骤

请告诉用户：

> 我需要一个 Exa API Key 来开启搜索功能。完全免费，每月 1000 次搜索。
>
> 步骤：
> 1. 打开 https://exa.ai
> 2. 点击 "Get API Key" 或 "Sign Up"
> 3. 用 Google 账号或邮箱注册
> 4. 注册后在 Dashboard 页面复制你的 API Key
> 5. 把 Key 发给我
>
> 大概 30 秒就能搞定。

## Agent 收到 key 后的操作

1. 写入配置：`config.set("exa_api_key", key)`
2. 测试：运行一次搜索确认可用
3. 反馈："✅ 全网搜索已开启！现在我可以帮你搜索全网、Reddit 和 Twitter 了。"
