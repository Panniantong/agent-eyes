# YouTube

Use Agent Reach for normalized video metadata, subtitle/caption availability, and thumbnail references. Use `yt-dlp` directly when you need transcript files, downloads, or other extractor-specific features.

```powershell
agent-reach collect --channel youtube --operation read --input "https://www.youtube.com/watch?v=VIDEO_ID" --json
```

The normalized item includes video diagnostics such as `extras.duration_seconds`, `extras.thumbnail_url`, item-level `media_references`, `extras.subtitle_languages`, `extras.automatic_caption_languages`, `extras.has_subtitles`, `extras.has_automatic_captions`, and `extras.source_hints`. Agent Reach does not download video binaries, extract frames, run OCR, or transcribe audio.

```powershell
yt-dlp --dump-single-json "https://www.youtube.com/watch?v=VIDEO_ID"
yt-dlp --skip-download --write-auto-sub --sub-langs "en.*,ja.*" -o "%(id)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

If `agent-reach doctor` warns about the JS runtime, run the fix command shown there before retrying.
