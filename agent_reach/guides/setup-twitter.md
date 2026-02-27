# Twitter 高级功能配置指南（xreach CLI）

Twitter 基础阅读通过 Jina Reader 免费可用，无需配置。

高级功能需要 xreach CLI：

- 搜索推文（`xreach search`）
- 读取完整推文和对话链（`xreach tweet`、`xreach thread`）
- 用户时间线（`xreach tweets`）

xreach 是免费开源工具（npm 包 xreach-cli），但需要你的 Twitter 账号 cookie。

## 快速配置

1. 检查 xreach 是否安装：

```bash
which xreach && echo "installed" || echo "not installed"
```

2. 安装 xreach：

```bash
npm install -g xreach-cli
```

3. 测试是否配置好：

```bash
AUTH_TOKEN="xxx" CT0="yyy" xreach search "test" -n 1
```

## 获取 Cookie（Cookie-Editor 方式，推荐）

1. 安装 [Cookie-Editor](https://cookie-editor.com/) 浏览器扩展
2. 登录 x.com
3. 点击 Cookie-Editor 图标 → Export → 复制全部
4. 运行配置命令：

```bash
agent-reach configure twitter-cookies "粘贴的 cookie JSON"
```

这会自动提取 `auth_token` 和 `ct0`，并写入环境变量。

## 手动设置 Cookie

如果你已经知道 `auth_token` 和 `ct0`：

1. 安装 xreach（如果没装）：`npm install -g xreach-cli`

2. 设置环境变量：

```bash
export AUTH_TOKEN="你的auth_token"
export CT0="你的ct0"
```

3. 测试：

```bash
xreach search "test" --auth-token "$AUTH_TOKEN" --ct0 "$CT0" -n 1
```

## 代理配置

> xreach CLI 内置代理支持，通过 `--proxy` 参数传入：

```bash
xreach search "test" --auth-token "$AUTH_TOKEN" --ct0 "$CT0" --proxy "http://user:pass@host:port"
```

也支持代理轮换文件：

```bash
xreach search "test" --auth-token "$AUTH_TOKEN" --ct0 "$CT0" --proxy-file proxies.txt
```
