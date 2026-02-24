# -*- coding: utf-8 -*-
"""
YouTube video fetcher — three-tier content extraction:

1. yt-dlp auto-subtitles (fastest, best quality for subtitled videos)
2. yt-dlp audio download → Groq Whisper API transcription (for non-subtitled videos)
3. Jina Reader fallback (page description only)

Requires: yt-dlp installed (brew install yt-dlp / pip install yt-dlp)
Optional: GROQ_API_KEY env var for Whisper transcription
"""

import re
import os
import subprocess
import tempfile
from loguru import logger
from typing import Dict, Any

from agent_eyes.fetchers.jina import fetch_via_jina


def _extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else ""


def _get_subtitles_via_ytdlp(url: str, lang: str = "en") -> str:
    """
    Download auto-generated subtitles using yt-dlp.
    Returns subtitle text, or empty string if unavailable.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "sub")

        cmd = [
            "yt-dlp",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", lang,
            "--sub-format", "srt",
            "--skip-download",
            "-o", output_path,
            url,
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            logger.warning("yt-dlp not found. Install with: brew install yt-dlp")
            return ""
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp subtitle download timed out")
            return ""

        for ext in [f".{lang}.srt", f".{lang}.vtt"]:
            sub_file = output_path + ext
            if os.path.exists(sub_file):
                return _parse_srt(sub_file)

    return ""


def _parse_srt(filepath: str) -> str:
    """Parse SRT file into clean text (strip timestamps and sequence numbers)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    text_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        if not line or line.isdigit() or '-->' in line:
            continue
        if line.startswith('[') and line.endswith(']'):
            continue
        if line not in seen:
            seen.add(line)
            text_lines.append(line)

    return " ".join(text_lines)


def _transcribe_via_whisper(url: str) -> str:
    """
    Download audio with yt-dlp and transcribe via Groq Whisper API.

    Requires: GROQ_API_KEY env var + yt-dlp + ffmpeg installed.
    Groq Whisper limit: 25MB audio file.
    Returns transcript text, or empty string if unavailable.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.info("GROQ_API_KEY not set, skipping Whisper transcription")
        return ""

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "audio.%(ext)s")

        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "m4a",
            "--audio-quality", "5",
            "-o", output_template,
            "--no-playlist",
            url,
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except FileNotFoundError:
            logger.warning("yt-dlp not found for audio download")
            return ""
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp audio download timed out")
            return ""

        # Find the downloaded audio file
        audio_path = os.path.join(tmpdir, "audio.m4a")
        if not os.path.exists(audio_path):
            for f in os.listdir(tmpdir):
                if f.startswith("audio."):
                    audio_path = os.path.join(tmpdir, f)
                    break
            else:
                logger.warning("No audio file downloaded")
                return ""

        file_size = os.path.getsize(audio_path)
        if file_size > 25 * 1024 * 1024:
            logger.warning(f"Audio file too large ({file_size // 1024 // 1024}MB > 25MB limit)")
            return ""

        logger.info(f"Transcribing {file_size // 1024}KB audio via Groq Whisper...")

        import requests
        try:
            with open(audio_path, "rb") as f:
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": (os.path.basename(audio_path), f, "audio/mp4")},
                    data={"model": "whisper-large-v3", "response_format": "text"},
                    timeout=120,
                )

            if response.status_code == 200:
                transcript = response.text.strip()
                logger.info(f"Whisper transcript: {len(transcript)} chars")
                return transcript
            else:
                logger.warning(f"Groq Whisper API error: {response.status_code} {response.text[:200]}")
                return ""
        except Exception as e:
            logger.warning(f"Whisper transcription failed: {e}")
            return ""


async def fetch_youtube(url: str, sub_lang: str = "en") -> Dict[str, Any]:
    """
    Fetch YouTube video content with three-tier extraction.

    Strategy:
    1. yt-dlp auto-subtitles (full transcript, fastest)
    2. yt-dlp audio + Groq Whisper API (for non-subtitled videos)
    3. Jina Reader fallback (page description only)

    Args:
        url: YouTube video URL
        sub_lang: Subtitle language code (default: "en")

    Returns:
        Dict with: title, description, author, url, video_id, has_transcript, platform
    """
    logger.info(f"Fetching YouTube: {url}")
    video_id = _extract_video_id(url)

    # Step 1: Get metadata via Jina (fast, always works)
    jina_data = fetch_via_jina(url)
    title = jina_data["title"]

    # Step 2: Try yt-dlp auto-subtitles
    logger.info(f"Extracting subtitles ({sub_lang})...")
    transcript = _get_subtitles_via_ytdlp(url, lang=sub_lang)

    # Step 3: No subtitles? Try Whisper transcription
    if not transcript:
        logger.info("No subtitles available, trying Whisper transcription...")
        transcript = _transcribe_via_whisper(url)

    if transcript:
        logger.info(f"Got transcript: {len(transcript)} chars")
        content = transcript
        has_transcript = True
    else:
        logger.info("No transcript available, using page description")
        content = jina_data["content"]
        has_transcript = False

    return {
        "title": title,
        "description": content,
        "author": jina_data.get("author", ""),
        "url": url,
        "video_id": video_id,
        "has_transcript": has_transcript,
        "platform": "youtube",
    }
