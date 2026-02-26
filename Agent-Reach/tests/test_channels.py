# -*- coding: utf-8 -*-
"""Tests for the channel system."""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from agent_reach.channels import get_channel_for_url, get_channel, get_all_channels
from agent_reach.channels.base import ReadResult, SearchResult


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

    def test_get_channel_by_name(self):
        ch = get_channel("github")
        assert ch is not None
        assert ch.name == "github"

    def test_all_channels_registered(self):
        channels = get_all_channels()
        names = [ch.name for ch in channels]
        assert "web" in names
        assert "github" in names
        assert "twitter" in names


class TestReadResult:
    def test_to_dict(self):
        r = ReadResult(title="Test", content="Body", url="https://example.com", platform="web")
        d = r.to_dict()
        assert d["title"] == "Test"
        assert d["content"] == "Body"
        assert d["platform"] == "web"

    def test_to_dict_optional_fields(self):
        r = ReadResult(title="T", content="C", url="u", author="A", date="2025-01-01")
        d = r.to_dict()
        assert d["author"] == "A"
        assert d["date"] == "2025-01-01"


class TestSearchResult:
    def test_to_dict(self):
        r = SearchResult(title="Test", url="https://example.com", snippet="A snippet")
        d = r.to_dict()
        assert d["title"] == "Test"
        assert d["snippet"] == "A snippet"


class TestGitHubChannel:
    def test_can_handle(self):
        ch = get_channel("github")
        assert ch.can_handle("https://github.com/user/repo")
        assert not ch.can_handle("https://example.com")

    @patch("agent_reach.channels.github.shutil.which", return_value="/usr/bin/gh")
    @patch("agent_reach.channels.github.subprocess.run")
    @pytest.mark.asyncio
    async def test_search_with_gh(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="user/repo\tA test repo\t\tpython\n",
            stderr="",
        )
        ch = get_channel("github")
        results = await ch.search("test query")
        assert len(results) >= 1
        assert results[0].title == "user/repo"

    @patch("agent_reach.channels.github.shutil.which", return_value=None)
    @pytest.mark.asyncio
    async def test_search_without_gh_raises(self, mock_which):
        ch = get_channel("github")
        with pytest.raises(ValueError, match="gh CLI"):
            await ch.search("test query")


class TestExaSearch:
    @patch("agent_reach.channels.base.Channel._mcporter_has", return_value=True)
    @patch("agent_reach.channels.base.Channel._mcporter_call")
    @pytest.mark.asyncio
    async def test_search(self, mock_call, mock_has):
        mock_call.return_value = (
            "Title: Result\n"
            "URL: https://example.com\n"
            "Text: snippet\n"
        )
        ch = get_channel("exa_search")
        results = await ch.search("test")
        assert len(results) == 1
        assert results[0].title == "Result"


def _make_httpx_async_client_mock(response_mock):
    """Build an AsyncClient context manager mock that returns response_mock on get()."""
    client_mock = MagicMock()
    client_mock.get = AsyncMock(return_value=response_mock)
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)
    cls_mock = MagicMock(return_value=client_mock)
    return cls_mock


class TestRedditChannel:
    def test_can_handle(self):
        ch = get_channel("reddit")
        assert ch.can_handle("https://reddit.com/r/python")
        assert not ch.can_handle("https://example.com")

    @pytest.mark.asyncio
    async def test_read_post(self):
        import httpx
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {"data": {"children": [{"data": {
                "title": "Test Post",
                "author": "testuser",
                "selftext": "Test content",
                "score": 100,
                "subreddit": "python",
            }}]}},
            {"data": {"children": []}},
        ]

        with patch("agent_reach.channels.reddit.httpx.AsyncClient",
                   _make_httpx_async_client_mock(mock_resp)):
            ch = get_channel("reddit")
            result = await ch.read("https://reddit.com/r/python/comments/abc123/test")

        assert result.title == "Test Post"
        assert "Test content" in result.content
        assert result.author == "u/testuser"

    @pytest.mark.asyncio
    async def test_read_403_returns_friendly_message(self):
        import httpx

        mock_resp = MagicMock()
        mock_resp.status_code = 403
        http_err = httpx.HTTPStatusError("403", request=MagicMock(), response=mock_resp)
        mock_resp.raise_for_status.side_effect = http_err

        with patch("agent_reach.channels.reddit.httpx.AsyncClient",
                   _make_httpx_async_client_mock(mock_resp)):
            ch = get_channel("reddit")
            result = await ch.read("https://reddit.com/r/python")

        assert "403" in result.content or "blocked" in result.content.lower()


# ── New test classes ──


class TestWebChannel:
    def test_can_handle(self):
        ch = get_channel("web")
        assert ch.can_handle("https://example.com")
        assert ch.can_handle("https://anything.io/path?q=1")

    @pytest.mark.asyncio
    async def test_read(self):
        import httpx
        body = "# My Article\n\nSome content here."
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = body

        with patch("agent_reach.channels.web.httpx.AsyncClient",
                   _make_httpx_async_client_mock(mock_resp)):
            ch = get_channel("web")
            result = await ch.read("https://example.com")

        assert result.title == "My Article"
        assert "Some content" in result.content
        assert result.platform == "web"

    @pytest.mark.asyncio
    async def test_read_error_returns_result(self):
        import httpx

        client_mock = MagicMock()
        client_mock.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        client_mock.__aenter__ = AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = AsyncMock(return_value=False)

        with patch("agent_reach.channels.web.httpx.AsyncClient", return_value=client_mock):
            ch = get_channel("web")
            result = await ch.read("https://example.com")

        assert "⚠️" in result.content
        assert result.platform == "web"


class TestYouTubeChannel:
    def test_can_handle(self):
        ch = get_channel("youtube")
        assert ch.can_handle("https://youtube.com/watch?v=abc")
        assert ch.can_handle("https://youtu.be/abc")
        assert not ch.can_handle("https://example.com")

    @patch("agent_reach.channels.youtube.shutil.which", return_value=None)
    @pytest.mark.asyncio
    async def test_read_without_ytdlp_raises(self, mock_which):
        ch = get_channel("youtube")
        with pytest.raises(RuntimeError, match="yt-dlp"):
            await ch.read("https://youtube.com/watch?v=abc")

    @patch("agent_reach.channels.youtube.subprocess.run")
    def test_get_info(self, mock_run):
        info = {"title": "Test Video", "uploader": "TestChannel", "duration_string": "5:00"}
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(info))
        ch = get_channel("youtube")
        result = ch._get_info("https://youtube.com/watch?v=abc")
        assert result["title"] == "Test Video"

    @patch("agent_reach.channels.youtube.shutil.which", return_value="/usr/bin/yt-dlp")
    @patch("agent_reach.channels.youtube.subprocess.run")
    @pytest.mark.asyncio
    async def test_search(self, mock_run, mock_which):
        items = [
            {"id": "vid1", "title": "Video 1", "channel": "Chan1",
             "duration_string": "3:00", "view_count": 1000},
        ]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\n".join(json.dumps(i) for i in items),
        )
        ch = get_channel("youtube")
        results = await ch.search("test query")
        assert len(results) == 1
        assert results[0].title == "Video 1"
        assert "youtube.com/watch?v=vid1" in results[0].url


class TestBilibiliChannel:
    def test_can_handle(self):
        ch = get_channel("bilibili")
        assert ch.can_handle("https://www.bilibili.com/video/BV1xx")
        assert ch.can_handle("https://b23.tv/abc")
        assert not ch.can_handle("https://example.com")

    @patch("agent_reach.channels.bilibili.subprocess.run")
    def test_search_ytdlp(self, mock_run):
        items = [
            {"id": "BV1xx", "title": "B站视频", "uploader": "UP主", "view_count": 5000,
             "webpage_url": "https://www.bilibili.com/video/BV1xx"},
        ]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\n".join(json.dumps(i) for i in items),
        )
        ch = get_channel("bilibili")
        results = ch._search_ytdlp("test", 5)
        assert len(results) == 1
        assert results[0].title == "B站视频"

    @patch("agent_reach.channels.bilibili.subprocess.run")
    def test_search_ytdlp_timeout_returns_empty(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="yt-dlp", timeout=60)
        ch = get_channel("bilibili")
        results = ch._search_ytdlp("test", 5)
        assert results == []


class TestMCPChannels:
    @pytest.mark.parametrize("channel_name,url", [
        ("xiaohongshu", "https://www.xiaohongshu.com/explore/abc123"),
        ("linkedin", "https://www.linkedin.com/in/johndoe"),
        ("bosszhipin", "https://www.zhipin.com/job_detail/abc.html"),
        ("instagram", "https://www.instagram.com/p/abc123"),
    ])
    def test_can_handle(self, channel_name, url):
        ch = get_channel(channel_name)
        assert ch.can_handle(url)

    @pytest.mark.parametrize("channel_name", [
        "xiaohongshu", "linkedin", "bosszhipin",
    ])
    def test_check_returns_valid_tuple(self, channel_name):
        ch = get_channel(channel_name)
        with patch.object(ch, "_mcporter_has", return_value=False):
            status, message = ch.check()
        assert status in ("ok", "warn", "off", "error")
        assert isinstance(message, str)
        assert len(message) > 0

    @pytest.mark.asyncio
    async def test_xhs_read_without_mcporter(self):
        ch = get_channel("xiaohongshu")
        with patch.object(ch, "_mcporter_has", return_value=False):
            result = await ch.read("https://www.xiaohongshu.com/explore/abc123")
        assert "⚠️" in result.content
        assert result.platform == "xiaohongshu"
