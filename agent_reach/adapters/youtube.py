# -*- coding: utf-8 -*-
"""YouTube collection adapter."""

from __future__ import annotations

import json
import time

from agent_reach.results import CollectionResult, build_item, parse_timestamp

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
        item = build_item(
            item_id=raw.get("id") or url,
            kind="video",
            title=raw.get("title"),
            url=raw.get("webpage_url") or raw.get("original_url") or url,
            text=raw.get("description"),
            author=raw.get("channel") or raw.get("uploader"),
            published_at=parse_timestamp(raw.get("upload_date") or raw.get("timestamp")),
            source=self.channel,
            extras={
                "duration_seconds": raw.get("duration"),
                "duration_text": raw.get("duration_string"),
                "view_count": raw.get("view_count"),
                "like_count": raw.get("like_count"),
                "comment_count": raw.get("comment_count"),
                "channel_url": raw.get("channel_url"),
                "uploader_url": raw.get("uploader_url"),
                "subtitle_languages": subtitle_langs,
            },
        )
        return self.ok_result(
            "read",
            items=[item],
            raw=raw,
            meta=self.make_meta(value=url, limit=limit, started_at=started_at),
        )
