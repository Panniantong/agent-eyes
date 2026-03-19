# -*- coding: utf-8 -*-
"""Tests for channel registry basics and health checks."""

import json
import shutil
import subprocess
from urllib.error import URLError

from agent_reach.channels import get_all_channels, get_channel
from agent_reach.channels.v2ex import V2EXChannel
from agent_reach.channels.xianyu import XianyuChannel
from agent_reach.channels.xiaohongshu import XiaoHongShuChannel


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
        assert "xianyu" in names


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

            def read(self):
                return b"[]"

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

    # ------------------------------------------------------------------ #
    # get_hot_topics
    # ------------------------------------------------------------------ #

    def test_get_hot_topics_returns_list(self, monkeypatch):
        import urllib.request

        fake_data = [
            {
                "id": 111,
                "title": "Python 3.13 发布了",
                "url": "https://www.v2ex.com/t/111",
                "replies": 42,
                "content": "发布公告内容",
                "created": 1700000000,
                "node": {"name": "python", "title": "Python"},
            },
            {
                "id": 222,
                "title": "Rust 好学吗",
                "url": "https://www.v2ex.com/t/222",
                "replies": 10,
                "content": "",
                "created": 1700000001,
                "node": {"name": "rust", "title": "Rust"},
            },
        ]

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def read(self):
                return json.dumps(fake_data).encode()

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: FakeResponse())
        topics = V2EXChannel().get_hot_topics(limit=5)
        assert len(topics) == 2
        assert topics[0]["id"] == 111
        assert topics[0]["title"] == "Python 3.13 发布了"
        assert topics[0]["replies"] == 42
        assert topics[0]["node_name"] == "python"
        assert topics[0]["node_title"] == "Python"
        assert topics[0]["created"] == 1700000000

    def test_get_hot_topics_respects_limit(self, monkeypatch):
        import urllib.request

        fake_data = [
            {"id": i, "title": f"Topic {i}", "url": f"https://v2ex.com/t/{i}", "replies": i,
             "content": "", "created": 1700000000 + i, "node": {"name": "tech", "title": "Tech"}}
            for i in range(10)
        ]

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return json.dumps(fake_data).encode()

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: FakeResponse())
        topics = V2EXChannel().get_hot_topics(limit=3)
        assert len(topics) == 3

    def test_get_hot_topics_truncates_content(self, monkeypatch):
        import urllib.request

        long_content = "A" * 300
        fake_data = [
            {"id": 1, "title": "Long post", "url": "https://v2ex.com/t/1", "replies": 0,
             "content": long_content, "created": 1700000000, "node": {"name": "tech", "title": "Tech"}}
        ]

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return json.dumps(fake_data).encode()

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: FakeResponse())
        topics = V2EXChannel().get_hot_topics(limit=1)
        assert len(topics[0]["content"]) == 200

    # ------------------------------------------------------------------ #
    # get_node_topics
    # ------------------------------------------------------------------ #

    def test_get_node_topics(self, monkeypatch):
        import urllib.request

        fake_data = [
            {
                "id": 333,
                "title": "Flask 部署问题",
                "url": "https://www.v2ex.com/t/333",
                "replies": 5,
                "content": "求帮助",
                "created": 1710000000,
                "node": {"name": "python", "title": "Python"},
            }
        ]

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return json.dumps(fake_data).encode()

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: FakeResponse())
        topics = V2EXChannel().get_node_topics("python")
        assert len(topics) == 1
        assert topics[0]["id"] == 333
        assert topics[0]["node_name"] == "python"
        assert topics[0]["title"] == "Flask 部署问题"
        assert topics[0]["created"] == 1710000000

    # ------------------------------------------------------------------ #
    # get_topic
    # ------------------------------------------------------------------ #

    def test_get_topic_returns_detail_and_replies(self, monkeypatch):
        import urllib.request

        topic_data = [
            {
                "id": 999,
                "title": "测试帖子",
                "url": "https://www.v2ex.com/t/999",
                "content": "帖子正文",
                "replies": 2,
                "node": {"name": "qna", "title": "问与答"},
                "member": {"username": "alice"},
                "created": 1700000000,
            }
        ]
        replies_data = [
            {
                "member": {"username": "bob"},
                "content": "第一条回复",
                "created": 1700000100,
            },
            {
                "member": {"username": "carol"},
                "content": "第二条回复",
                "created": 1700000200,
            },
        ]

        call_count = {"n": 0}

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return json.dumps(self._payload).encode()

        def fake_urlopen(req, timeout=None):
            url = req.full_url
            if "replies" in url:
                return FakeResponse(replies_data)
            return FakeResponse(topic_data)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        result = V2EXChannel().get_topic(999)

        assert result["id"] == 999
        assert result["title"] == "测试帖子"
        assert result["author"] == "alice"
        assert result["node_name"] == "qna"
        assert len(result["replies"]) == 2
        assert result["replies"][0]["author"] == "bob"
        assert result["replies"][1]["content"] == "第二条回复"

    def test_get_topic_handles_empty_replies(self, monkeypatch):
        import urllib.request

        topic_data = [
            {
                "id": 1,
                "title": "孤独帖子",
                "url": "https://www.v2ex.com/t/1",
                "content": "",
                "replies": 0,
                "node": {"name": "offtopic", "title": "水"},
                "member": {"username": "dave"},
                "created": 0,
            }
        ]

        class FakeResponse:
            def __init__(self, payload): self._payload = payload
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return json.dumps(self._payload).encode()

        def fake_urlopen(req, timeout=None):
            if "replies" in req.full_url:
                return FakeResponse([])
            return FakeResponse(topic_data)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        result = V2EXChannel().get_topic(1)
        assert result["replies"] == []

    # ------------------------------------------------------------------ #
    # get_user
    # ------------------------------------------------------------------ #

    def test_get_user_returns_profile(self, monkeypatch):
        import urllib.request

        fake_user = {
            "id": 42,
            "username": "alice",
            "url": "https://www.v2ex.com/member/alice",
            "website": "https://alice.dev",
            "twitter": "alice_tw",
            "psn": "",
            "github": "alice",
            "btc": "",
            "location": "Shanghai",
            "bio": "Python dev",
            "avatar_large": "https://cdn.v2ex.com/avatars/alice_large.png",
            "created": 1500000000,
        }

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self): return json.dumps(fake_user).encode()

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: FakeResponse())
        user = V2EXChannel().get_user("alice")

        assert user["id"] == 42
        assert user["username"] == "alice"
        assert user["github"] == "alice"
        assert user["location"] == "Shanghai"
        assert "alice_large.png" in user["avatar"]

    # ------------------------------------------------------------------ #
    # search
    # ------------------------------------------------------------------ #

    def test_search_returns_unavailable_notice(self):
        result = V2EXChannel().search("python asyncio")
        assert len(result) == 1
        assert "error" in result[0]
        assert "V2EX" in result[0]["error"]


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


class TestXianyuChannel:
    # ------------------------------------------------------------------ #
    # can_handle
    # ------------------------------------------------------------------ #

    def test_can_handle_goofish_urls(self):
        ch = XianyuChannel()
        assert ch.can_handle("https://www.goofish.com/item?id=123")
        assert ch.can_handle("https://goofish.com/search?q=iphone")
        assert not ch.can_handle("https://github.com/user/repo")
        assert not ch.can_handle("https://taobao.com/item/123")

    def test_can_handle_xianyu_taobao_urls(self):
        ch = XianyuChannel()
        assert ch.can_handle("https://xianyu.taobao.com/item_detail.htm?id=123")
        assert not ch.can_handle("https://www.taobao.com/item/123")

    # ------------------------------------------------------------------ #
    # check — node missing
    # ------------------------------------------------------------------ #

    def test_check_off_when_node_missing(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: None)
        status, msg = XianyuChannel().check()
        assert status == "off"
        assert "Node.js" in msg
        assert "nodejs.org" in msg

    # ------------------------------------------------------------------ #
    # check — mcporter missing
    # ------------------------------------------------------------------ #

    def test_check_off_when_mcporter_missing(self, monkeypatch):
        def fake_which(cmd):
            return "/usr/bin/node" if cmd == "node" else None

        monkeypatch.setattr(shutil, "which", fake_which)
        status, msg = XianyuChannel().check()
        assert status == "off"
        assert "mcporter" in msg

    # ------------------------------------------------------------------ #
    # check — xianyu not in mcporter config
    # ------------------------------------------------------------------ #

    def test_check_off_when_xianyu_not_configured(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        def fake_run(cmd, **kwargs):
            if "config" in cmd and "list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "douyin\nxiaohongshu\n", "")
            raise AssertionError(f"unexpected command: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, msg = XianyuChannel().check()
        assert status == "off"
        assert "mcporter config add" in msg

    def test_check_off_accepts_goofish_alias_in_config(self, monkeypatch):
        """If mcporter config list shows 'goofish' instead of 'xianyu', must not error."""
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        def fake_run(cmd, **kwargs):
            if "config" in cmd and "list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "goofish\ndouyin\n", "")
            # mcporter list goofish
            assert cmd == ["/usr/bin/mcporter", "list", "goofish"]
            return subprocess.CompletedProcess(cmd, 0, "search_items\nget_item_detail\n", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, _ = XianyuChannel().check()
        assert status == "ok"

    # ------------------------------------------------------------------ #
    # check — mcporter config exception
    # ------------------------------------------------------------------ #

    def test_check_off_when_config_list_raises(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        def fake_run(cmd, **kwargs):
            raise OSError("mcporter crashed")

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, msg = XianyuChannel().check()
        assert status == "off"
        assert "mcporter" in msg

    # ------------------------------------------------------------------ #
    # check — ok path
    # ------------------------------------------------------------------ #

    def test_check_ok_when_mcp_list_returns_tools(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        def fake_run(cmd, **kwargs):
            if "config" in cmd and "list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "xianyu\ndouyin\n", "")
            # mcporter list xianyu
            return subprocess.CompletedProcess(cmd, 0, "search_items\nget_item_detail\n", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, msg = XianyuChannel().check()
        assert status == "ok"
        assert "商品搜索" in msg

    # ------------------------------------------------------------------ #
    # check — warn paths
    # ------------------------------------------------------------------ #

    def test_check_warn_when_mcp_list_empty(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        def fake_run(cmd, **kwargs):
            if "config" in cmd and "list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "xianyu\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, msg = XianyuChannel().check()
        assert status == "warn"
        assert "mcp-goofish" in msg

    def test_check_warn_when_mcp_list_nonzero_returncode(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        def fake_run(cmd, **kwargs):
            if "config" in cmd and "list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "xianyu\n", "")
            return subprocess.CompletedProcess(cmd, 1, "", "error")

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, msg = XianyuChannel().check()
        assert status == "warn"

    def test_check_warn_when_mcp_list_times_out(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        call_count = {"n": 0}

        def fake_run(cmd, **kwargs):
            if "config" in cmd and "list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "xianyu\n", "")
            raise subprocess.TimeoutExpired(cmd, 15)

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, msg = XianyuChannel().check()
        assert status == "warn"
        assert "login" in msg or "超时" in msg

    def test_check_warn_when_mcp_list_raises_generic(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcporter")

        def fake_run(cmd, **kwargs):
            if "config" in cmd and "list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "xianyu\n", "")
            raise OSError("connection reset")

        monkeypatch.setattr(subprocess, "run", fake_run)
        status, msg = XianyuChannel().check()
        assert status == "warn"
        assert "mcp-goofish" in msg

    # ------------------------------------------------------------------ #
    # channel metadata
    # ------------------------------------------------------------------ #

    def test_channel_metadata(self):
        ch = XianyuChannel()
        assert ch.name == "xianyu"
        assert ch.tier == 2
        assert "mcp-goofish" in ch.backends
        assert ch.description  # non-empty

    def test_check_returns_tuple_of_str(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: None)
        result = XianyuChannel().check()
        assert isinstance(result, tuple) and len(result) == 2
        status, msg = result
        assert isinstance(status, str)
        assert isinstance(msg, str) and msg.strip()
