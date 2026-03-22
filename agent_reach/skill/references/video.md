# 视频/播客

YouTube、B站、小宇宙播客的字幕和转录。

## YouTube (yt-dlp)

### 获取视频元数据

```bash
yt-dlp --dump-json "URL"
```

### 下载字幕

```bash
# 下载字幕 (不下载视频)
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"

# 然后读取 .vtt 文件
cat /tmp/VIDEO_ID.*.vtt
```

### 搜索视频

```bash
yt-dlp --dump-json "ytsearch5:query"
```

## B站 / Bilibili (yt-dlp)

### 获取视频元数据

```bash
yt-dlp --dump-json "https://www.bilibili.com/video/BVxxx"
```

### 下载字幕

```bash
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --convert-subs vtt --skip-download -o "/tmp/%(id)s" "URL"
```

> **注意**: 服务器 IP 可能遇到 412 错误。使用 `--cookies-from-browser chrome` 或配置代理。

## 小宇宙播客 / Xiaoyuzhou Podcast

### 转录单集播客

```bash
# 输出 Markdown 文件到 /tmp/
~/.agent-reach/tools/xiaoyuzhou/transcribe.sh "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID"
```

### 前置要求

1. **ffmpeg**: `brew install ffmpeg`
2. **Groq API Key** (免费): https://console.groq.com/keys
3. **配置 Key**: `agent-reach configure groq-key YOUR_KEY`
4. **首次运行**: `agent-reach install --env=auto` 安装工具

### 检查状态

```bash
agent-reach doctor
```

> 输出 Markdown 文件默认保存到 `/tmp/`。

## 抖音视频解析

```bash
# 解析视频信息
mcporter call 'douyin.parse_douyin_video_info(share_link: "https://v.douyin.com/xxx/")'

# 获取无水印下载链接
mcporter call 'douyin.get_douyin_download_link(share_link: "https://v.douyin.com/xxx/")'
```

> 详见 [social.md](social.md#抖音--douyin)

## 选择指南

| 场景 | 推荐工具 |
|-----|---------|
| YouTube 字幕 | yt-dlp |
| B站字幕 | yt-dlp |
| 播客转录 | 小宇宙 transcribe.sh |
| 抖音视频解析 | douyin MCP |
