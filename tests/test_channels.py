# -*- coding: utf-8 -*-
"""Tests for channel routing and registry."""

from agent_reach.channels import get_channel_for_url, get_channel, get_all_channels


class TestChannelRouting:
    def test_github_url(self):
        ch = get_channel_for_url("https://github.com/openai/gpt-4")
        assert ch.name == "github"

    def test_twitter_url(self):
        ch = get_channel_for_url("https://x.com/elonmusk/status/123")
        assert ch.name == "twitter"

    def test_youtube_url(self):
        ch = get_channel_for_url("https://youtube.com/watch?v=abc")
        assert ch.name == "youtube"

    def test_reddit_url(self):
        ch = get_channel_for_url("https://reddit.com/r/test")
        assert ch.name == "reddit"

    def test_bilibili_url(self):
        ch = get_channel_for_url("https://bilibili.com/video/BV1xx")
        assert ch.name == "bilibili"

    def test_rss_url(self):
        ch = get_channel_for_url("https://example.com/feed.xml")
        assert ch.name == "rss"

    def test_generic_url_fallback(self):
        ch = get_channel_for_url("https://example.com")
        assert ch.name == "web"

    def test_non_string_url_fallback(self):
        ch = get_channel_for_url(None)  # type: ignore[arg-type]
        assert ch.name == "web"


class TestChannelRegistry:
    def test_get_channel_by_name(self):
        ch = get_channel("github")
        assert ch is not None
        assert ch.name == "github"

    def test_get_unknown_channel_returns_none(self):
        assert get_channel("not-exists") is None

    def test_all_channels_registered(self):
        channels = get_all_channels()
        names = [ch.name for ch in channels]
        assert "web" in names
        assert "github" in names
        assert "twitter" in names
