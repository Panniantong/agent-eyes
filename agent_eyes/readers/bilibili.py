# -*- coding: utf-8 -*-
"""Bilibili video fetcher — uses official web API."""

import re
import requests
from loguru import logger
from typing import Dict, Any


API_URL = "https://api.bilibili.com/x/web-interface/view"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


async def fetch_bilibili(url_or_bv: str) -> Dict[str, Any]:
    """Fetch Bilibili video metadata via official API."""
    logger.info(f"Fetching Bilibili: {url_or_bv}")

    bv_id = url_or_bv
    if "bilibili.com" in url_or_bv or "b23.tv" in url_or_bv:
        match = re.search(r'BV\w+', url_or_bv)
        if match:
            bv_id = match.group()
        else:
            raise ValueError(f"Cannot extract BV ID from: {url_or_bv}")

    resp = requests.get(API_URL, params={"bvid": bv_id}, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise ValueError(f"Bilibili API error: {data.get('message')}")

    video = data["data"]
    return {
        "title": video.get("title", ""),
        "description": video.get("desc", ""),
        "author": video.get("owner", {}).get("name", ""),
        "url": f"https://www.bilibili.com/video/{bv_id}",
        "cover": video.get("pic", ""),
        "bvid": bv_id,
        "duration": video.get("duration", 0),
        "view_count": video.get("stat", {}).get("view", 0),
        "platform": "bilibili",
    }
