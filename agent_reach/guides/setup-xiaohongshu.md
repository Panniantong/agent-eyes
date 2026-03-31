# 小红书配置指南

## 功能说明
读取和搜索小红书笔记。通过 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 实现（⭐9K+，Go 语言，内置 Chrome 浏览器）。

## 前置条件
- Docker（用来运行 xiaohongshu-mcp 服务）
- mcporter CLI（MCP 协议桥接工具）

## Agent 可自动完成的步骤

### 1. 安装 mcporter
```bash
npm install -g mcporter
```

### 2. 启动 xiaohongshu-mcp 服务
```bash
docker run -d \
  --name xiaohongshu-mcp \
  -p 18060:18060 \
  xpzouying/xiaohongshu-mcp
```

> 如需代理（服务器部署推荐）：
> ```bash
> docker run -d \
>   --name xiaohongshu-mcp \
>   -p 18060:18060 \
>   -e XHS_PROXY=http://user:pass@ip:port \
>   xpzouying/xiaohongshu-mcp
> ```

### 3. 注册到 mcporter
```bash
mcporter config add xiaohongshu http://localhost:18060/mcp
```

### 4. 验证
```bash
agent-reach doctor
```

应该看到小红书显示为 ✅ 或 ⚠️（MCP 已连接但未登录）。

## 需要用户手动做的步骤

如果 doctor 显示"MCP 已连接但未登录"，需要导入 cookies：

> **推荐方式：Cookie-Editor 浏览器导出（最可靠）**
>
> 1. 在 Chrome 中安装 [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) 扩展
> 2. 浏览器登录 xiaohongshu.com
> 3. 点击 Cookie-Editor 图标 → Export → Header String
> 4. 把导出的字符串发给 Agent，运行：`agent-reach configure xhs-cookies "导出的cookie字符串"`
>
> **注意**：`http://localhost:18060` 根路径可能返回 404，这是正常的——MCP 服务在 `/mcp` 路径。
> 不要依赖 QR 扫码登录，Docker 容器内的 QR 登录页面不一定可用，且 cookies 不会自动共享到 MCP 服务。

## 常见问题

**Q: Docker 容器重启后 cookie 丢了？**
A: 挂载数据卷持久化：
```bash
docker run -d \
  --name xiaohongshu-mcp \
  -p 18060:18060 \
  -v xhs-data:/app/data \
  xpzouying/xiaohongshu-mcp
```

**Q: 服务器上小红书提示 IP 风险？**
A: 加代理参数 `-e XHS_PROXY=http://user:pass@ip:port`，推荐住宅代理。

**Q: Docker 镜像不支持 ARM64 / Apple Silicon？**
A: 上游镜像暂无 ARM64 版本，两种解决办法：

方法一：使用 Rosetta 模拟运行（推荐，最简单）
```bash
docker run -d \
  --name xiaohongshu-mcp \
  -p 18060:18060 \
  --platform linux/amd64 \
  xpzouying/xiaohongshu-mcp
```

方法二：从源码编译原生 ARM64 版本
```bash
git clone https://github.com/xpzouying/xiaohongshu-mcp
cd xiaohongshu-mcp
docker build -t xiaohongshu-mcp .
docker run -d --name xiaohongshu-mcp -p 18060:18060 xiaohongshu-mcp
```

**Q: 我不想用 Docker？**
A: 可以从源码编译：https://github.com/xpzouying/xiaohongshu-mcp
