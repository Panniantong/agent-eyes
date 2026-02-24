# Reddit 代理配置指南

## 功能说明
Reddit 封锁了大量服务器 IP，直接访问会返回 403。需要 ISP 代理（Residential/ISP Proxy）才能读取完整的 Reddit 帖子和评论。

**注意**：即使没有代理，也可以通过 Exa 搜索找到 Reddit 内容（只需要配 Exa API key）。代理只是用于读取完整帖子+评论。

## Agent 可自动完成的步骤

1. 检查当前状态：
```bash
agent-eyes doctor | grep "Reddit"
```

2. 如果用户提供了代理，测试连通性：
```bash
curl -s --proxy "用户提供的代理" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  "https://www.reddit.com/r/test.json?limit=1" \
  -o /dev/null -w "%{http_code}"
```
返回 200 = 可用，403 = 代理被封，其他 = 配置错误

3. 写入配置：
```python
from agent_eyes.config import Config
c = Config()
c.set("reddit_proxy", "http://用户名:密码@IP:端口")
```

## 需要用户手动做的步骤

请告诉用户：

> 要完整阅读 Reddit 帖子和评论，需要一个 ISP 代理（约 $3-10/月）。
>
> 推荐代理服务商（选一个就行）：
> 1. **Smartproxy** (https://smartproxy.com) — ISP 代理，按流量计费
> 2. **Bright Data** (https://brightdata.com) — 大厂，ISP 代理
> 3. **IPRoyal** (https://iproyal.com) — 便宜，适合入门
> 4. **ProxyEmpire** (https://proxyempire.io) — 有 Reddit 专用代理
>
> 购买时选择：
> - 类型：**ISP Proxy**（不要选 Datacenter，会被封）
> - 地区：**美国**
> - 协议：**HTTP**
>
> 购买后你会得到一个代理地址，格式类似：
> `http://用户名:密码@IP地址:端口号`
>
> 把这个地址发给我就行。
>
> ⚠️ 如果不想花钱，可以跳过。我仍然可以通过搜索引擎找到 Reddit 上的内容，只是不能读完整的帖子和评论。

## Agent 收到代理后的操作

1. 测试代理：用 curl 测试 reddit.com 是否返回 200
2. 如果成功，写入配置：`config.set("reddit_proxy", proxy_url)`
3. 反馈："✅ Reddit 完整阅读已开启！现在我可以读取 Reddit 帖子和所有评论了。"
4. 如果失败，告诉用户："❌ 这个代理无法访问 Reddit，请检查代理是否有效，或换一个试试。"
