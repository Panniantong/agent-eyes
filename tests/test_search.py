# -*- coding: utf-8 -*-
"""Tests for Agent Eyes search modules."""

import pytest
from unittest.mock import patch, MagicMock

from agent_eyes.config import Config


@pytest.fixture
def tmp_config(tmp_path):
    c = Config(config_path=tmp_path / "config.yaml")
    c.set("exa_api_key", "test-key")
    return c


class TestExaSearch:
    @patch("agent_eyes.search.exa.requests.post")
    @pytest.mark.asyncio
    async def test_search_web(self, mock_post, tmp_config):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "text": "This is a test snippet",
                    "publishedDate": "2025-01-01",
                    "score": 0.95,
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from agent_eyes.search.exa import search_web
        results = await search_web("test query", config=tmp_config)

        assert len(results) == 1
        assert results[0]["title"] == "Test Result"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["snippet"] == "This is a test snippet"

    def test_search_web_requires_key(self):
        from agent_eyes.search.exa import _get_api_key
        with pytest.raises(ValueError, match="Exa API key"):
            _get_api_key(Config(config_path="/tmp/nonexistent/config.yaml"))


class TestRedditSearch:
    @patch("agent_eyes.search.exa.requests.post")
    @pytest.mark.asyncio
    async def test_search_reddit(self, mock_post, tmp_config):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from agent_eyes.search.reddit import search_reddit
        results = await search_reddit("test", config=tmp_config)

        # Verify it searched site:reddit.com
        call_args = mock_post.call_args
        query = call_args[1]["json"]["query"]
        assert "site:reddit.com" in query

    @patch("agent_eyes.search.exa.requests.post")
    @pytest.mark.asyncio
    async def test_search_reddit_with_sub(self, mock_post, tmp_config):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from agent_eyes.search.reddit import search_reddit
        await search_reddit("test", subreddit="LocalLLaMA", config=tmp_config)

        call_args = mock_post.call_args
        query = call_args[1]["json"]["query"]
        assert "site:reddit.com/r/LocalLLaMA" in query


class TestGitHubSearch:
    @patch("agent_eyes.search.github.requests.get")
    @pytest.mark.asyncio
    async def test_search_github(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [
                {
                    "full_name": "owner/repo",
                    "html_url": "https://github.com/owner/repo",
                    "description": "A test repo",
                    "stargazers_count": 100,
                    "forks_count": 20,
                    "language": "Python",
                    "updated_at": "2025-01-01",
                    "topics": ["ai"],
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from agent_eyes.search.github import search_github
        results = await search_github("test")

        assert len(results) == 1
        assert results[0]["name"] == "owner/repo"
        assert results[0]["stars"] == 100

    @patch("agent_eyes.search.github.requests.get")
    @pytest.mark.asyncio
    async def test_search_github_with_language(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from agent_eyes.search.github import search_github
        await search_github("test", language="python")

        call_args = mock_get.call_args
        assert "language:python" in call_args[1]["params"]["q"]


class TestTwitterSearch:
    @patch("agent_eyes.search.twitter.shutil.which", return_value=None)
    @patch("agent_eyes.search.exa.requests.post")
    @pytest.mark.asyncio
    async def test_search_twitter_exa_fallback(self, mock_post, mock_which, tmp_config):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from agent_eyes.search.twitter import search_twitter
        results = await search_twitter("test", config=tmp_config)

        call_args = mock_post.call_args
        query = call_args[1]["json"]["query"]
        assert "site:x.com" in query
