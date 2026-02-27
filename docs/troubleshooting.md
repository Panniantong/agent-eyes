# 常见问题排查

## Twitter/X: xreach CLI "fetch failed"

**症状：** `xreach search` 或其他命令返回 "fetch failed"

**原因：** xreach CLI 使用 Node.js 的 `undici` 库发请求。如果你的网络环境需要代理才能访问 x.com，需要明确传入代理参数。

**解决方案：**

### 方案 1：使用 --proxy 参数

```bash
xreach search "test" --auth-token "$AUTH_TOKEN" --ct0 "$CT0" --proxy "http://user:pass@host:port"
```

### 方案 2：使用全局代理工具

让代理工具接管所有网络流量，这样 xreach 的请求也会走代理：

```bash
# macOS — ClashX / Surge 开启"增强模式"
# Linux — proxychains 或 tun2socks
proxychains xreach search "test" -n 1
```

### 方案 3：不用 xreach，用 Exa 搜索替代

xreach 不可用时，可以直接用 Exa 搜索 Twitter 内容：

```bash
mcporter call 'exa.web_search_exa(query: "site:x.com 搜索词", numResults: 5)'
```

### 方案 4：设置 HTTP_PROXY 环境变量

```bash
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

xreach search "test"
```

> ⚠️ 注意：Node.js 原生 fetch 不一定读取这些环境变量，推荐用方案 1 的 --proxy 参数。
