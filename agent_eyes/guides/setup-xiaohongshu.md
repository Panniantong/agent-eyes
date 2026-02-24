# 小红书配置指南

## 功能说明
读取小红书笔记内容。需要 Playwright（浏览器自动化）和一次性登录。

## Agent 可自动完成的步骤

1. 检查 Playwright 是否安装：
```bash
python3 -c "import playwright; print('installed')" 2>&1
```

2. 安装 Playwright + 浏览器：
```bash
pip install playwright
playwright install chromium
```

3. 检查是否已有登录态：
```bash
# 检查 cookie 文件是否存在
ls ~/.agent-eyes/xhs_cookies.json 2>/dev/null
```

## 需要用户手动做的步骤

请告诉用户：

> 小红书需要登录一次（之后会记住你的登录状态）。
>
> 我现在会打开一个浏览器窗口，显示小红书登录页面。你需要：
> 1. 用手机小红书 App 扫描屏幕上的二维码
> 2. 在手机上确认登录
> 3. 看到首页后告诉我"登录好了"
>
> 之后就不需要再登录了（除非 cookie 过期，大约 1-3 个月）。

## Agent 收到确认后的操作

1. 保存浏览器 cookie 到 `~/.agent-eyes/xhs_cookies.json`
2. 测试：读取一条小红书笔记
3. 反馈："✅ 小红书已配置！现在我可以读取小红书笔记了。"
