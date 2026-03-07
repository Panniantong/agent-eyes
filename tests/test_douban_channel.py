# -*- coding: utf-8 -*-
"""Tests for Douban channel."""

import pytest
from agent_reach.channels.douban import DoubanChannel


@pytest.fixture
def ch():
    return DoubanChannel()


# ── metadata ──

def test_metadata(ch):
    assert ch.name == "douban"
    assert ch.tier == 0
    assert len(ch.backends) >= 2


def test_description_covers_music(ch):
    assert "音乐" in ch.description


# ── can_handle: positive ──

@pytest.mark.parametrize("url", [
    "https://movie.douban.com/subject/1292052/",
    "https://book.douban.com/subject/2567698/",
    "https://www.douban.com/group/explore",
    "https://m.douban.com/movie/subject/1292052/",
    "https://music.douban.com/subject/1234567/",
    "https://www.douban.com/people/ahbei/",
    "https://www.douban.com/doulist/1234/",
])
def test_can_handle_positive(ch, url):
    assert ch.can_handle(url)


# ── can_handle: negative ──

@pytest.mark.parametrize("url", [
    "https://www.imdb.com/title/tt0111161/",
    "https://www.bilibili.com/video/BV123",
    "https://book.google.com/books?id=abc",
    "https://www.goodreads.com/book/show/1234",
    "https://example.com/douban.com",
    "https://notdouban.com/subject/123/",
    "https://douban.com.evil.cn/fake",
])
def test_can_handle_negative(ch, url):
    assert not ch.can_handle(url)


# ── check ──

def test_check_returns_tuple(ch):
    status, msg = ch.check()
    assert status in ("ok", "warn")
    assert isinstance(msg, str)


def test_check_with_config(ch):
    """check() should accept config dict without error."""
    status, msg = ch.check(config={})
    assert status in ("ok", "warn")


def test_check_proxy_config(ch):
    """check() should read douban_proxy from config."""
    status, msg = ch.check(config={"douban_proxy": "http://127.0.0.1:10808"})
    assert status in ("ok", "warn")


# ── registration ──

def test_registered():
    from agent_reach.channels import ALL_CHANNELS
    names = [c.name for c in ALL_CHANNELS]
    assert "douban" in names
