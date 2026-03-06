# -*- coding: utf-8 -*-
"""Tests for Toutiao and Tencent News channels."""

import pytest
from agent_reach.channels.toutiao import ToutiaoChannel
from agent_reach.channels.tencent_news import TencentNewsChannel


# ── Toutiao ──────────────────────────────────────────────────

class TestToutiaoCanHandle:
    ch = ToutiaoChannel()

    @pytest.mark.parametrize("url", [
        "https://www.toutiao.com/article/7612594790944932406/",
        "https://m.toutiao.com/i7612594790944932406/",
        "https://toutiao.com/group/7612594790944932406/",
        "https://www.toutiao.com/a7612594790944932406/",
        "https://www.toutiao.com/w/7612594790944932406/",
        "https://www.toutiao.com/search/?keyword=AI",
    ])
    def test_toutiao_urls(self, url):
        assert self.ch.can_handle(url)

    @pytest.mark.parametrize("url", [
        "https://www.baidu.com",
        "https://news.qq.com/rain/a/123",
        "https://www.weibo.com/123",
    ])
    def test_non_toutiao_urls(self, url):
        assert not self.ch.can_handle(url)


class TestToutiaoMetadata:
    ch = ToutiaoChannel()

    def test_name(self):
        assert self.ch.name == "toutiao"

    def test_tier(self):
        assert self.ch.tier == 0

    def test_backends(self):
        assert "Feed API" in self.ch.backends


class TestToutiaoCheck:
    ch = ToutiaoChannel()

    def test_check_returns_tuple(self):
        status, msg = self.ch.check()
        assert status in ("ok", "warn", "off", "error")
        assert isinstance(msg, str)


# ── Tencent News ─────────────────────────────────────────────

class TestTencentNewsCanHandle:
    ch = TencentNewsChannel()

    @pytest.mark.parametrize("url", [
        "https://new.qq.com/rain/a/20260306A06IWP00",
        "https://news.qq.com/rain/a/20260306A05U6C00",
        "https://view.inews.qq.com/a/20260306A06IWP00",
        "https://xw.qq.com/cmsid/20260306A06IWP00",
        "https://new.qq.com/omn/20260306/20260306A05U6C00.html",
    ])
    def test_qq_news_urls(self, url):
        assert self.ch.can_handle(url)

    @pytest.mark.parametrize("url", [
        "https://www.qq.com",
        "https://mail.qq.com",
        "https://www.toutiao.com/article/123",
        "https://kuai.qq.com/page/123",
        "https://y.qq.com/n/ryqq/player",
    ])
    def test_non_qq_news_urls(self, url):
        assert not self.ch.can_handle(url)


class TestTencentNewsMetadata:
    ch = TencentNewsChannel()

    def test_name(self):
        assert self.ch.name == "tencent_news"

    def test_tier(self):
        assert self.ch.tier == 0

    def test_backends(self):
        assert "Hot Ranking API" in self.ch.backends


class TestTencentNewsCheck:
    ch = TencentNewsChannel()

    def test_check_returns_tuple(self):
        status, msg = self.ch.check()
        assert status in ("ok", "warn", "off", "error")
        assert isinstance(msg, str)


# ── Registration ─────────────────────────────────────────────

class TestRegistration:
    def test_toutiao_in_registry(self):
        from agent_reach.channels import ALL_CHANNELS
        names = [ch.name for ch in ALL_CHANNELS]
        assert "toutiao" in names

    def test_tencent_news_in_registry(self):
        from agent_reach.channels import ALL_CHANNELS
        names = [ch.name for ch in ALL_CHANNELS]
        assert "tencent_news" in names
