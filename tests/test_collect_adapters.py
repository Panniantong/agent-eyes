# -*- coding: utf-8 -*-
"""Tests for the external collection adapters."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agent_reach.adapters.base import BaseAdapter
from agent_reach.adapters.bluesky import BlueskyAdapter
from agent_reach.adapters.exa_search import ExaSearchAdapter
from agent_reach.adapters.github import GitHubAdapter
from agent_reach.adapters.hatena_bookmark import HatenaBookmarkAdapter
from agent_reach.adapters.qiita import QiitaAdapter
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


def test_hatena_bookmark_adapter_success(config, monkeypatch):
    class FakeResponse:
        status_code = 200
        text = '{"ok":true}'

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {
                "eid": "123",
                "title": "Example Domain",
                "url": "https://example.com/",
                "entry_url": "https://b.hatena.ne.jp/entry/s/example.com/",
                "count": 12,
                "screenshot": "https://example.com/image.png",
                "bookmarks": [
                    {"user": "alice", "comment": "useful", "timestamp": "2026/04/10 10:00", "tags": []}
                ],
                "related": [
                    {
                        "eid": "related-1",
                        "title": "Related Entry",
                        "url": "https://example.com/related",
                        "entry_url": "https://b.hatena.ne.jp/entry/s/example.com/related",
                        "count": 5,
                    }
                ],
            }

    class FakeRequests:
        RequestException = RuntimeError

        @staticmethod
        def get(_url, params=None, headers=None, timeout=None):
            return FakeResponse()

    monkeypatch.setattr("agent_reach.adapters.hatena_bookmark._import_requests", lambda: FakeRequests)

    payload = HatenaBookmarkAdapter(config=config).read("https://example.com", limit=2)

    assert payload["ok"] is True
    assert payload["items"][0]["extras"]["bookmark_count"] == 12
    assert payload["items"][1]["kind"] == "related_page"


def test_hatena_bookmark_adapter_handles_missing_entry(config, monkeypatch):
    class EmptyResponse:
        status_code = 200
        text = "null"

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return None

    class FakeRequests:
        RequestException = RuntimeError

        @staticmethod
        def get(_url, params=None, headers=None, timeout=None):
            return EmptyResponse()

    adapter = HatenaBookmarkAdapter(config=config)
    monkeypatch.setattr("agent_reach.adapters.hatena_bookmark._import_requests", lambda: FakeRequests)
    monkeypatch.setattr(adapter, "_bookmark_count", lambda _url: 0)

    payload = adapter.read("https://example.com")

    assert payload["ok"] is True
    assert payload["items"][0]["extras"]["bookmark_count"] == 0


def test_bluesky_adapter_success(config, monkeypatch):
    class PublicApi403Response:
        status_code = 403
        text = "forbidden"

        @staticmethod
        def json():
            raise ValueError("not json")

    class ApiResponse:
        status_code = 200
        text = '{"posts":[]}'

        @staticmethod
        def json():
            return {
                "posts": [
                    {
                        "uri": "at://did:plc:abc/app.bsky.feed.post/3abc",
                        "cid": "cid-1",
                        "author": {"handle": "openai.com", "displayName": "OpenAI"},
                        "record": {
                            "text": "OpenAI shipped a thing",
                            "createdAt": "2026-04-10T00:00:00Z",
                        },
                        "likeCount": 10,
                        "replyCount": 2,
                        "repostCount": 3,
                        "quoteCount": 1,
                        "bookmarkCount": 4,
                        "indexedAt": "2026-04-10T00:00:01Z",
                        "labels": [],
                        "embed": {
                            "$type": "app.bsky.embed.images#view",
                            "images": [
                                {
                                    "fullsize": "https://cdn.bsky.app/img/feed_fullsize/plain/image-1.jpg",
                                    "thumb": "https://cdn.bsky.app/img/feed_thumbnail/plain/image-1.jpg",
                                    "alt": "Example image",
                                    "aspectRatio": {"width": 4, "height": 3},
                                }
                            ],
                        },
                    }
                ]
            }

    class FakeRequests:
        RequestException = RuntimeError

        @staticmethod
        def get(url, headers=None, timeout=None):
            if "public.api.bsky.app" in url:
                return PublicApi403Response()
            return ApiResponse()

    monkeypatch.setattr("agent_reach.adapters.bluesky._import_requests", lambda: FakeRequests)

    payload = BlueskyAdapter(config=config).search("OpenAI", limit=1)

    assert payload["ok"] is True
    assert payload["items"][0]["author"] == "openai.com"
    assert payload["meta"]["api_base_url"] == "https://api.bsky.app"
    assert payload["meta"]["fallback_used"] is True
    assert payload["items"][0]["extras"]["media"][0]["type"] == "image"
    assert payload["items"][0]["extras"]["media"][0]["aspect_ratio"] == {"width": 4, "height": 3}


def test_bluesky_adapter_normalizes_nested_video_embed(config, monkeypatch):
    class ApiResponse:
        status_code = 200
        text = '{"posts":[]}'

        @staticmethod
        def json():
            return {
                "posts": [
                    {
                        "uri": "at://did:plc:abc/app.bsky.feed.post/3abc",
                        "cid": "cid-1",
                        "author": {"handle": "openai.com", "displayName": "OpenAI"},
                        "record": {
                            "text": "Video post",
                            "createdAt": "2026-04-10T00:00:00Z",
                        },
                        "embed": {
                            "$type": "app.bsky.embed.recordWithMedia#view",
                            "media": {
                                "$type": "app.bsky.embed.video#view",
                                "playlist": "https://video.bsky.app/playlist.m3u8",
                                "thumbnail": "https://video.bsky.app/thumb.jpg",
                                "alt": "Video alt",
                                "aspectRatio": {"width": 9, "height": 16},
                            },
                        },
                    }
                ]
            }

    class FakeRequests:
        RequestException = RuntimeError

        @staticmethod
        def get(url, headers=None, timeout=None):
            return ApiResponse()

    monkeypatch.setattr("agent_reach.adapters.bluesky._import_requests", lambda: FakeRequests)

    payload = BlueskyAdapter(config=config).search("OpenAI", limit=1)

    assert payload["ok"] is True
    assert payload["items"][0]["extras"]["media"][0]["type"] == "video"
    assert payload["items"][0]["extras"]["media"][0]["playlist_url"] == "https://video.bsky.app/playlist.m3u8"


def test_qiita_adapter_success(config, monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "[]"
        headers = {"Total-Count": "42"}

        @staticmethod
        def json():
            return [
                {
                    "id": "abc123",
                    "title": "Qiita article",
                    "url": "https://qiita.com/Qiita/items/abc123",
                    "body": "markdown body",
                    "created_at": "2026-04-10T00:00:00+09:00",
                    "updated_at": "2026-04-10T01:00:00+09:00",
                    "likes_count": 10,
                    "stocks_count": 20,
                    "comments_count": 3,
                    "reactions_count": 4,
                    "page_views_count": 50,
                    "private": False,
                    "tags": [{"name": "Python"}],
                    "user": {"id": "Qiita"},
                }
            ]

    class FakeRequests:
        RequestException = RuntimeError

        @staticmethod
        def get(_url, params=None, headers=None, timeout=None):
            return FakeResponse()

    monkeypatch.setattr("agent_reach.adapters.qiita._import_requests", lambda: FakeRequests)

    payload = QiitaAdapter(config=config).search("python", limit=1)

    assert payload["ok"] is True
    assert payload["items"][0]["author"] == "Qiita"
    assert payload["meta"]["total_count"] == "42"


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
    captured = {}

    def fake_run(command, timeout=120, env=None):
        captured["command"] = command
        return _cp(
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
        )

    monkeypatch.setattr(
        adapter,
        "run_command",
        fake_run,
    )

    payload = adapter.search("OpenAI", limit=1)

    assert payload["ok"] is True
    assert payload["items"][0]["author"] == "OpenAI"
    assert payload["items"][0]["url"] == "https://x.com/OpenAI/status/123"
    assert payload["items"][0]["extras"]["metrics"] == {"likes": 10}
    assert captured["command"][1:3] == ["search", "OpenAI"]


def test_twitter_adapter_search_translates_common_advanced_tokens(config, monkeypatch):
    adapter = TwitterAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "twitter")
    captured = {}

    def fake_run(command, timeout=120, env=None):
        captured["command"] = command
        return _cp(stdout=json.dumps({"ok": True, "data": []}))

    monkeypatch.setattr(adapter, "run_command", fake_run)

    payload = adapter.search("from:OpenAI has:media type:photos lang:ja", limit=5)

    assert payload["ok"] is True
    assert captured["command"] == [
        "twitter",
        "search",
        "--from",
        "OpenAI",
        "--has",
        "media",
        "--type",
        "photos",
        "--lang",
        "ja",
        "-n",
        "5",
        "--json",
    ]


def test_twitter_adapter_user_success(config, monkeypatch):
    adapter = TwitterAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "twitter")
    monkeypatch.setattr(
        adapter,
        "run_command",
        lambda command, timeout=120, env=None: _cp(
            stdout=json.dumps(
                {
                    "ok": True,
                    "data": {
                        "id": "4398626122",
                        "name": "OpenAI",
                        "screenName": "OpenAI",
                        "bio": "Research lab",
                        "followers": 100,
                        "following": 4,
                        "tweets": 10,
                        "likes": 5,
                        "verified": True,
                        "url": "https://openai.com",
                        "createdAtISO": "2015-12-06T22:51:08+00:00",
                    },
                }
            )
        ),
    )

    payload = adapter.user("@OpenAI")

    assert payload["ok"] is True
    assert payload["items"][0]["kind"] == "profile"
    assert payload["items"][0]["url"] == "https://x.com/OpenAI"
    assert payload["items"][0]["extras"]["followers"] == 100


def test_twitter_adapter_user_posts_success(config, monkeypatch):
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
                            "media": [{"type": "photo", "url": "https://pbs.twimg.com/media/a.png"}],
                        }
                    ],
                }
            )
        ),
    )

    payload = adapter.user_posts("https://x.com/OpenAI", limit=1)

    assert payload["ok"] is True
    assert payload["operation"] == "user_posts"
    assert payload["items"][0]["extras"]["media"][0]["type"] == "photo"


def test_twitter_adapter_tweet_success(config, monkeypatch):
    adapter = TwitterAdapter(config=config)
    monkeypatch.setattr(adapter, "command_path", lambda _name: "twitter")
    captured = {}

    def fake_run(command, timeout=120, env=None):
        captured["command"] = command
        return _cp(
            stdout=json.dumps(
                {
                    "ok": True,
                    "data": [
                        {
                            "id": "123",
                            "text": "OpenAI shipped a thing",
                            "author": {"screenName": "OpenAI", "name": "OpenAI"},
                            "createdAtISO": "2026-04-10T00:00:00Z",
                        }
                    ],
                }
            )
        )

    monkeypatch.setattr(adapter, "run_command", fake_run)

    payload = adapter.tweet("https://x.com/OpenAI/status/123", limit=1)

    assert payload["ok"] is True
    assert captured["command"][2] == "123"
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


def test_base_adapter_runtime_env_is_noninteractive_and_utf8(config, monkeypatch):
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    config.set("qiita_token", "qiita-token")

    env = BaseAdapter(config=config).runtime_env()

    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["PYTHONUTF8"] == "1"
    assert env["QIITA_TOKEN"] == "qiita-token"
