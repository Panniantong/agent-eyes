# YouTube

Use Agent Reach for normalized metadata, or `yt-dlp` directly when you need subtitles and other extractor-specific features.

```powershell
agent-reach collect --channel youtube --operation read --input "https://www.youtube.com/watch?v=VIDEO_ID" --json
```

```powershell
yt-dlp --dump-single-json "https://www.youtube.com/watch?v=VIDEO_ID"
yt-dlp --skip-download --write-auto-sub --sub-langs "en.*,ja.*" -o "%(id)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

If `agent-reach doctor` warns about the JS runtime, run the fix command shown there before retrying.
