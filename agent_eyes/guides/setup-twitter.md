# Twitter 高级功能配置指南（birdx）

## 功能说明
基础 Twitter 功能（搜索+读单条推文）无需配置，开箱即用。

高级功能需要 birdx：
- 查看用户时间线
- 深度搜索（更精确、更多结果）
- 读取完整线程（thread）
- 查看关注列表推文

birdx 是免费开源工具，但需要你的 Twitter 账号 cookie。

## Agent 可自动完成的步骤

1. 检查 birdx 是否安装：
```bash
which birdx && echo "installed" || echo "not installed"
```

2. 安装 birdx：
```bash
pip install birdx
```

3. 检查是否已配置 cookie：
```bash
birdx whoami 2>&1
```

4. 如果用户提供了 cookie，配置 birdx：
```bash
# birdx 的 cookie 配置文件位置
# 通常在 ~/.birdx/cookies.json 或通过环境变量
export TWITTER_AUTH_TOKEN="用户提供的auth_token"
export TWITTER_CT0="用户提供的ct0"
```

5. 测试：
```bash
birdx search "test" -n 1
```

## 需要用户手动做的步骤

请告诉用户：

> Twitter 高级功能需要你的 Twitter 账号 cookie（完全免费）。
>
> 步骤：
> 1. 用 Chrome 打开 https://x.com 并确保你已登录
> 2. 按 **F12** 打开开发者工具（Mac 按 Cmd+Option+I）
> 3. 点击顶部的 **Application**（应用）标签
> 4. 左侧找到 **Cookies** → **https://x.com**
> 5. 在列表中找到以下两个值，双击复制：
>    - **auth_token** — 一串字母数字
>    - **ct0** — 一串字母数字
> 6. 把这两个值发给我
>
> ⚠️ 这些 cookie 让我能以你的身份读取推文（只读）。我不会发推、点赞或做任何操作。
> ⚠️ cookie 大约 1-3 个月会过期，届时需要重新导出。

## Agent 收到 cookie 后的操作

1. 安装 birdx（如果没装）：`pip install birdx`
2. 配置 cookie：写入 birdx 配置
3. 测试：`birdx whoami` 确认身份
4. 反馈："✅ Twitter 高级功能已开启！你的账号是 @xxx。现在我可以查看时间线、读取线程了。"
5. 如果失败："❌ Cookie 无效或已过期，请重新导出。"
