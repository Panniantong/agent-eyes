# -*- coding: utf-8 -*-
"""Tests for the external collection adapters."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agent_reach.adapters.exa_search import ExaSearchAdapter
from agent_reach.adapters.github import GitHubAdapter
from agent_reach.adapters.rss import RSSAdapter
from agent_reach.adapters.twitter import TwitterAdapter
from agent_reach.adapters.web import WebAdapter
from agent_reach.adapters.youtube import YouTubeAdapter
from agent_reach.config import Config


@pytest.fixture
def config(tmp_path):
    return Config(config_path=tmp_path / "config.yaml")


def _cp(stdout="", stderr="", returncode=0):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def test_web_adapter_success(config, monkeypatch):
    class FakeResponse:
        text = (
            "Title: Example Domain\n\n"
            "Published Time: 2026-04-10T00:00:00Z\n\n"
            "Markdown Content:\n"
            "# Example Domain\n\nThis is a test page.\n"
        )

        def raise_for_status(self):
            return None

    class FakeRequests:
        RequestException = RuntimeError

        @staticmethod
        def get(_url, headers=None, timeout=None):
            return FakeResponse()

    monkeypatch.setattr("agent_reach.adapters.web._import_requests", lambda: FakeRequests)

    payload = WebAdapter(config=config).read("example.com")

    assert payload["ok"] is True
    assert payload["items"][0]["title"] == "Example Domain"
    assert payload["items"][0]["published_at"] == "2026-04-10T00:00:00Z"
    assert "This is a test page." in payload["items"][0]["text"]


def test_web_adapter_http_error(config, monkeypatch):
    class FakeRequests:
        RequestException = RuntimeError

        @staticmethod
        def get(_url, headers=None, timeout=None):
            raise RuntimeError("boom")

    monkeypatch.setattr("agent_reach.adapters.web._import_requests", lambda: FakeRequests)

    payload = WebAdapter(config=config).read("example.com")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "http_error"


def test_exa_adapter_success(config, monkeypatch):
    adapter = ExaSearchAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "mcporter")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=120, env=None: _cp(
            stdout=json.dumps(
                {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Title: Example result\n"
                                "URL: https://example.com/post\n"
                                "Published: 2026-04-10T00:00:00Z\n"
                                "Author: Alice\n"
                                "Highlights:\nA useful summary\n"
                            ),
                        }
                    ]
                }
            )
        ),
    )

    payload = adapter.search("example", limit=1)

    assert payload["ok"] is True
    assert payload["items"][0]["title"] == "Example result"
    assert payload["items"][0]["author"] == "Alice"


def test_exa_adapter_missing_dependency(config):
    adapter = ExaSearchAdapter(config=config)
    adapter.command_path = lambda _name: None

    payload = adapter.search("example")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "missing_dependency"


def test_exa_adapter_reports_invalid_response_when_normalization_fails(config, monkeypatch):
    adapter = ExaSearchAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "mcporter")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=120, env=None: _cp(
            stdout=json.dumps({"content": [{"type": "text", "text": "unexpected format"}]})
        ),
    )

    payload = adapter.search("example", limit=1)

    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_response"


def test_github_adapter_read_success(config, monkeypatch):
    adapter = GitHubAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "gh")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=60, env=None: _cp(
            stdout=json.dumps(
                {
                    "name": "openai-python",
                    "nameWithOwner": "openai/openai-python",
                    "description": "Python SDK",
                    "url": "https://github.com/openai/openai-python",
                    "owner": {"login": "openai"},
                    "updatedAt": "2026-04-10T00:00:00Z",
                    "createdAt": "2020-01-01T00:00:00Z",
                    "homepageUrl": "https://example.com",
                    "stargazerCount": 1,
                    "forkCount": 2,
                    "licenseInfo": {"name": "MIT"},
                    "primaryLanguage": {"name": "Python"},
                    "isPrivate": False,
                    "isArchived": False,
                    "defaultBranchRef": {"name": "main"},
                    "repositoryTopics": [{"name": "openai"}],
                }
            )
        ),
    )

    payload = adapter.read("openai/openai-python")

    assert payload["ok"] is True
    assert payload["items"][0]["id"] == "openai/openai-python"
    assert payload["items"][0]["extras"]["default_branch"] == "main"


def test_github_adapter_invalid_json(config, monkeypatch):
    adapter = GitHubAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "gh")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=60, env=None: _cp(stdout="not json"),
    )

    payload = adapter.search("agent reach", limit=1)

    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_response"


def test_youtube_adapter_success(config, monkeypatch):
    adapter = YouTubeAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "yt-dlp")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=120, env=None: _cp(
            stdout=json.dumps(
                {
                    "id": "abc123",
                    "title": "Example Video",
                    "webpage_url": "https://www.youtube.com/watch?v=abc123",
                    "description": "Video description",
                    "channel": "Example Channel",
                    "upload_date": "20260410",
                    "duration": 19,
                    "subtitles": {"en": [{}]},
                }
            )
        ),
    )

    payload = adapter.read("https://www.youtube.com/watch?v=abc123")

    assert payload["ok"] is True
    assert payload["items"][0]["kind"] == "video"
    assert payload["items"][0]["extras"]["subtitle_languages"] == ["en"]


def test_youtube_adapter_invalid_json(config, monkeypatch):
    adapter = YouTubeAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "yt-dlp")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=120, env=None: _cp(stdout="broken"),
    )

    payload = adapter.read("https://www.youtube.com/watch?v=abc123")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_response"


def test_rss_adapter_success(config, monkeypatch):
    parsed = SimpleNamespace(
        feed={"title": "Example Feed"},
        entries=[
            {
                "id": "entry-1",
                "title": "Example Entry",
                "link": "https://example.com/post",
                "summary": "Summary",
                "author": "Alice",
                "published": "2026-04-10T00:00:00Z",
            }
        ],
        bozo=False,
        status=200,
    )
    monkeypatch.setattr("agent_reach.adapters.rss.feedparser.parse", lambda url: parsed)

    payload = RSSAdapter(config=config).read("https://example.com/feed.xml", limit=1)

    assert payload["ok"] is True
    assert payload["meta"]["feed_title"] == "Example Feed"
    assert payload["items"][0]["author"] == "Alice"


def test_rss_adapter_parse_failure(config, monkeypatch):
    monkeypatch.setattr(
        "agent_reach.adapters.rss.feedparser.parse",
        lambda url: (_ for _ in ()).throw(RuntimeError("broken")),
    )

    payload = RSSAdapter(config=config).read("https://example.com/feed.xml")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "parse_failed"


def test_twitter_adapter_success(config, monkeypatch):
    adapter = TwitterAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "twitter")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=120, env=None: _cp(
            stdout=json.dumps(
                {
                    "ok": True,
                    "data": [
                        {
                            "id": "123",
                            "text": "OpenAI shipped a thing",
                            "author": {"screenName": "OpenAI", "name": "OpenAI"},
                            "createdAtISO": "2026-04-10T00:00:00Z",
                            "metrics": {"likes": 10},
                        }
                    ],
                }
            )
        ),
    )

    payload = adapter.search("OpenAI", limit=1)

    assert payload["ok"] is True
    assert payload["items"][0]["author"] == "OpenAI"
    assert payload["items"][0]["url"] == "https://x.com/OpenAI/status/123"


def test_twitter_adapter_not_authenticated(config, monkeypatch):
    adapter = TwitterAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "twitter")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=120, env=None: _cp(
            stderr="error:\n  code: not_authenticated\n",
            returncode=1,
        ),
    )

    payload = adapter.search("OpenAI", limit=1)

    assert payload["ok"] is False
    assert payload["error"]["code"] == "not_authenticated"
