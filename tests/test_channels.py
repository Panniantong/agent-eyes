# -*- coding: utf-8 -*-
"""Tests for channel registry basics and health checks."""

import shutil
import subprocess
from urllib.error import URLError

from agent_reach.channels import get_all_channels, get_channel
from agent_reach.channels.xiaohongshu import XiaoHongShuChannel
from agent_reach.channels.v2ex import V2EXChannel


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
        assert "v2ex" in names


class TestV2EXChannel:
    def test_can_handle_v2ex_urls(self):
        ch = V2EXChannel()
        assert ch.can_handle("https://www.v2ex.com/t/1234567")
        assert ch.can_handle("https://v2ex.com/go/python")
        assert not ch.can_handle("https://github.com/user/repo")
        assert not ch.can_handle("https://reddit.com/r/Python")

    def test_check_ok_when_api_reachable(self, monkeypatch):
        import urllib.request

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        monkeypatch.setattr(
            urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(),
        )
        status, msg = V2EXChannel().check()
        assert status == "ok"
        assert "公开 API 可用" in msg

    def test_check_warn_when_api_unreachable(self, monkeypatch):
        import urllib.request

        def raise_error(req, timeout=None):
            raise URLError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", raise_error)
        status, msg = V2EXChannel().check()
        assert status == "warn"
        assert "失败" in msg


class TestXiaoHongShuChannel:
    def test_reports_ok_when_server_health_is_ok(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/opt/homebrew/bin/mcporter")

        def fake_run(cmd, **kwargs):
            if cmd[:4] == ["/opt/homebrew/bin/mcporter", "config", "get", "xiaohongshu"]:
                return subprocess.CompletedProcess(cmd, 0, '{"name":"xiaohongshu"}', "")
            if cmd[:4] == ["/opt/homebrew/bin/mcporter", "list", "xiaohongshu", "--json"]:
                return subprocess.CompletedProcess(cmd, 0, '{"status": "ok"}', "")
            raise AssertionError(f"unexpected command: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        assert XiaoHongShuChannel().check() == (
            "ok",
            "MCP 已连接（阅读、搜索、发帖、评论、点赞）",
        )
