# -*- coding: utf-8 -*-
"""Tests for Hacker News channel."""

import pytest
from agent_reach.channels.hackernews import HackerNewsChannel


@pytest.fixture
def ch():
    return HackerNewsChannel()


# ── metadata ──

def test_metadata(ch):
    assert ch.name == "hackernews"
    assert ch.tier == 0
    assert "Firebase API" in ch.backends
    assert "Algolia Search" in ch.backends


# ── can_handle: positive ──

@pytest.mark.parametrize("url", [
    "https://news.ycombinator.com/",
    "https://news.ycombinator.com/item?id=47282736",
    "https://news.ycombinator.com/newest",
    "https://news.ycombinator.com/ask",
    "https://news.ycombinator.com/show",
    "https://news.ycombinator.com/jobs",
    "https://news.ycombinator.com/user?id=dang",
    "https://news.ycombinator.com/from?site=github.com",
    "https://hn.algolia.com/?query=AI+agent",
])
def test_can_handle_positive(ch, url):
    assert ch.can_handle(url)


# ── can_handle: negative ──

@pytest.mark.parametrize("url", [
    "https://www.reddit.com/r/programming/",
    "https://www.ycombinator.com/apply/",
    "https://medium.com/@user/article",
    "https://dev.to/user/article",
    "https://lobste.rs/",
    "https://news.google.com/",
    "https://example.com/news.ycombinator.com",
])
def test_can_handle_negative(ch, url):
    assert not ch.can_handle(url)


# ── check ──

def test_check_returns_tuple(ch):
    status, msg = ch.check()
    assert status in ("ok", "warn")
    assert isinstance(msg, str)


# ── registration ──

def test_registered():
    from agent_reach.channels import ALL_CHANNELS
    names = [c.name for c in ALL_CHANNELS]
    assert "hackernews" in names


# ── Firebase API live tests ──

class TestFirebaseAPI:
    """Live API tests — skipped if network unavailable."""

    @pytest.fixture(autouse=True)
    def _skip_if_offline(self):
        import urllib.request
        try:
            urllib.request.urlopen(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=5,
            )
        except Exception:
            pytest.skip("HN API unreachable")

    def test_topstories(self):
        import json
        import urllib.request
        with urllib.request.urlopen(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10,
        ) as r:
            ids = json.loads(r.read())
            assert isinstance(ids, list)
            assert len(ids) > 0

    def test_item(self):
        import json
        import urllib.request
        with urllib.request.urlopen(
            "https://hacker-news.firebaseio.com/v0/item/1.json",
            timeout=10,
        ) as r:
            item = json.loads(r.read())
            assert item["id"] == 1
            assert "by" in item

    def test_all_story_endpoints(self):
        import json
        import urllib.request
        for ep in ["topstories", "newstories", "beststories",
                    "askstories", "showstories", "jobstories"]:
            url = f"https://hacker-news.firebaseio.com/v0/{ep}.json"
            with urllib.request.urlopen(url, timeout=10) as r:
                ids = json.loads(r.read())
                assert isinstance(ids, list), f"{ep} returned non-list"


# ── Algolia Search live tests ──

class TestAlgoliaSearch:
    """Live Algolia HN Search tests."""

    @pytest.fixture(autouse=True)
    def _skip_if_offline(self):
        import urllib.request
        try:
            urllib.request.urlopen(
                "https://hn.algolia.com/api/v1/search?query=test&hitsPerPage=1",
                timeout=5,
            )
        except Exception:
            pytest.skip("Algolia HN API unreachable")

    def test_search_stories(self):
        import json
        import urllib.request
        url = ("https://hn.algolia.com/api/v1/search"
               "?query=python&tags=story&hitsPerPage=3")
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
            assert data["nbHits"] > 0
            assert len(data["hits"]) > 0
            hit = data["hits"][0]
            assert "title" in hit
            assert "points" in hit

    def test_search_comments(self):
        import json
        import urllib.request
        url = ("https://hn.algolia.com/api/v1/search"
               "?query=machine+learning&tags=comment&hitsPerPage=3")
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
            assert data["nbHits"] > 0
