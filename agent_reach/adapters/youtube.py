# -*- coding: utf-8 -*-
"""YouTube collection adapter."""

from __future__ import annotations

import json
import time

from agent_reach.media_references import build_media_reference, dedupe_media_references
from agent_reach.results import CollectionResult, build_item, parse_timestamp
from agent_reach.source_hints import video_source_hints

from .base import BaseAdapter


class YouTubeAdapter(BaseAdapter):
    """Read video metadata through yt-dlp."""

    channel = "youtube"
    operations = ("read",)

    def read(self, url: str, limit: int | None = None) -> CollectionResult:
        started_at = time.perf_counter()
        ytdlp = self.command_path("yt-dlp")
        if not ytdlp:
            return self.error_result(
                "read",
                code="missing_dependency",
                message="yt-dlp is missing. Install it with winget install --id yt-dlp.yt-dlp -e",
                meta=self.make_meta(value=url, limit=limit, started_at=started_at),
            )

        try:
            result = self.run_command(
                [
                    ytdlp,
                    "--dump-single-json",
                    "--no-playlist",
                    "--simulate",
                    url,
                ],
                timeout=120,
            )
        except Exception as exc:
            return self.error_result(
                "read",
                code="command_failed",
                message=f"YouTube read failed: {exc}",
                meta=self.make_meta(value=url, limit=limit, started_at=started_at),
            )

        raw_output = f"{result.stdout}\n{result.stderr}".strip()
        if result.returncode != 0:
            return self.error_result(
                "read",
                code="command_failed",
                message="yt-dlp did not complete cleanly",
                raw=raw_output,
                meta=self.make_meta(value=url, limit=limit, started_at=started_at),
                details={"returncode": result.returncode},
            )

        try:
            raw = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return self.error_result(
                "read",
                code="invalid_response",
                message="yt-dlp returned a non-JSON payload",
                raw=raw_output,
                meta=self.make_meta(value=url, limit=limit, started_at=started_at),
            )
        subtitle_langs = sorted((raw.get("subtitles") or {}).keys())
        automatic_caption_langs = sorted((raw.get("automatic_captions") or {}).keys())
        requested_subtitle_langs = sorted((raw.get("requested_subtitles") or {}).keys())
        thumbnails = raw.get("thumbnails") if isinstance(raw.get("thumbnails"), list) else []
        media_references = [
            reference
            for reference in [
                build_media_reference(
                    type="image",
                    url=raw.get("thumbnail"),
                    relation="thumbnail",
                    width=raw.get("thumbnail_width"),
                    height=raw.get("thumbnail_height"),
                    source_field="thumbnail",
                )
            ]
            if reference is not None
        ]
        for thumbnail in thumbnails:
            if not isinstance(thumbnail, dict):
                continue
            reference = build_media_reference(
                type="image",
                url=thumbnail.get("url"),
                relation="thumbnail",
                width=thumbnail.get("width"),
                height=thumbnail.get("height"),
                source_field="thumbnails[]",
            )
            if reference is not None:
                media_references.append(reference)
        published_at = parse_timestamp(raw.get("upload_date") or raw.get("timestamp"))
        item = build_item(
            item_id=raw.get("id") or url,
            kind="video",
            title=raw.get("title"),
            url=raw.get("webpage_url") or raw.get("original_url") or url,
            text=raw.get("description"),
            author=raw.get("channel") or raw.get("uploader"),
            published_at=published_at,
            source=self.channel,
            extras={
                "duration_seconds": raw.get("duration"),
                "duration_text": raw.get("duration_string"),
                "view_count": raw.get("view_count"),
                "like_count": raw.get("like_count"),
                "comment_count": raw.get("comment_count"),
                "channel_url": raw.get("channel_url"),
                "uploader_url": raw.get("uploader_url"),
                "thumbnail_url": raw.get("thumbnail"),
                "thumbnail_count": len(thumbnails),
                "media_references": dedupe_media_references(media_references),
                "subtitle_languages": subtitle_langs,
                "automatic_caption_languages": automatic_caption_langs,
                "has_subtitles": bool(subtitle_langs),
                "has_automatic_captions": bool(automatic_caption_langs),
                "requested_subtitle_languages": requested_subtitle_langs,
                "source_hints": video_source_hints(published_at),
            },
        )
        return self.ok_result(
            "read",
            items=[item],
            raw=raw,
            meta=self.make_meta(value=url, limit=limit, started_at=started_at),
        )
