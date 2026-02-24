# -*- coding: utf-8 -*-
"""
Telegram channel fetcher — uses Telethon.

Requires: pip install x-reader[telegram]
Requires: TG_API_ID + TG_API_HASH in .env
"""

import os
from datetime import datetime, timedelta, timezone
from loguru import logger
from typing import Dict, Any, List


async def fetch_telegram(
    channel: str,
    limit: int = 20,
    hours: int = 24,
    session_path: str = None,
) -> List[Dict[str, Any]]:
    """
    Fetch recent messages from a Telegram channel.

    Args:
        channel: Channel username (e.g. 'predictionmkt')
        limit: Max messages per channel
        hours: Only fetch messages from the last N hours
        session_path: Path to Telethon session file

    Returns:
        List of message dicts
    """
    try:
        from telethon import TelegramClient
        from telethon.tl.types import Message
    except ImportError:
        raise ImportError(
            "Telethon is required for Telegram fetching. "
            "Install with: pip install x-reader[telegram]"
        )

    api_id = os.getenv("TG_API_ID", "")
    api_hash = os.getenv("TG_API_HASH", "")

    if not api_id or not api_hash:
        raise ValueError("TG_API_ID and TG_API_HASH must be set in .env")

    session = session_path or os.getenv("TG_SESSION_PATH", "./tg_session")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    messages = []
    async with TelegramClient(session, int(api_id), api_hash) as client:
        logger.info(f"Fetching TG channel: {channel}")
        entity = await client.get_entity(channel)

        async for msg in client.iter_messages(entity, limit=limit):
            if not isinstance(msg, Message) or not msg.text:
                continue
            if msg.date < cutoff:
                break

            messages.append({
                "text": msg.text,
                "views": msg.views or 0,
                "date": msg.date.isoformat(),
                "url": f"https://t.me/{channel}/{msg.id}",
                "platform": "telegram",
            })

    logger.info(f"TG {channel}: {len(messages)} messages")
    return messages
