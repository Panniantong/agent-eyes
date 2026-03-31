# -*- coding: utf-8 -*-
"""Tests for DiscordChannel."""

from unittest.mock import MagicMock, patch

import pytest

from agent_reach.channels.discord import DiscordChannel, _get_invite_code


@pytest.fixture
def ch():
    return DiscordChannel()


class TestDiscordChannelAttributes:
    def test_name(self, ch):
        assert ch.name == "discord"

    def test_tier(self, ch):
        assert ch.tier == 0

    def test_backends(self, ch):
        assert ch.backends


class TestDiscordCanHandle:
    def test_discord_gg(self, ch):
        assert ch.can_handle("https://discord.gg/python")

    def test_discord_com(self, ch):
        assert ch.can_handle("https://discord.com/invite/rust")

    def test_discord_channel_url(self, ch):
        assert ch.can_handle("https://discord.com/channels/123/456")

    def test_rejects_other(self, ch):
        assert not ch.can_handle("https://www.slack.com")


class TestGetInviteCode:
    def test_discord_gg(self):
        assert _get_invite_code("https://discord.gg/python") == "python"

    def test_discord_com_invite(self):
        assert _get_invite_code("https://discord.com/invite/rust-lang") == "rust-lang"

    def test_trailing_slash(self):
        assert _get_invite_code("https://discord.gg/python/") == "python"

    def test_no_invite_code(self):
        assert _get_invite_code("https://discord.com/channels/123/456") == ""


class TestDiscordCheck:
    def test_check_ok_with_exa(self, ch):
        with patch("agent_reach.channels.discord._exa_available", return_value=True):
            status, msg = ch.check()
        assert status == "ok"
        assert "Exa" in msg

    def test_check_warn_without_exa(self, ch):
        with patch("agent_reach.channels.discord._exa_available", return_value=False):
            status, msg = ch.check()
        assert status == "warn"
        assert "Invite API" in msg


class TestDiscordRead:
    def test_read_invite_url(self, ch):
        mock_data = {
            "guild": {"name": "Python", "description": "The Python community"},
            "channel": {"name": "general"},
            "approximate_member_count": 400000,
            "approximate_presence_count": 30000,
        }
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = __import__("json").dumps(mock_data).encode()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = ch.read("https://discord.gg/python")

        assert "Python" in result
        assert "400,000" in result
        assert "general" in result
