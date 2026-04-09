# -*- coding: utf-8 -*-
"""Tests for the Twitter/X channel."""

from unittest.mock import Mock, patch

from agent_reach.channels.twitter import TwitterChannel


def _cp(stdout="", stderr="", returncode=0):
    mock = Mock()
    mock.stdout = stdout
    mock.stderr = stderr
    mock.returncode = returncode
    return mock


def test_check_reports_warn_when_not_installed():
    with patch("agent_reach.channels.twitter.find_command", return_value=None), patch(
        "shutil.which", return_value=None
    ):
        status, message = TwitterChannel().check()
    assert status == "warn"
    assert "uv tool install twitter-cli" in message


def test_check_reports_ok_when_authenticated():
    channel = TwitterChannel()
    with patch(
        "agent_reach.channels.twitter.find_command",
        return_value="/usr/local/bin/twitter",
    ), patch(
        "subprocess.run",
        return_value=_cp(stdout="ok: true\nusername: testuser\n", returncode=0),
    ):
        status, message = channel.check()
    assert status == "ok"
    assert "tweet reads" in message


def test_check_reports_warn_when_not_authenticated():
    channel = TwitterChannel()
    with patch(
        "agent_reach.channels.twitter.find_command",
        return_value="/usr/local/bin/twitter",
    ), patch(
        "subprocess.run",
        return_value=_cp(stderr="ok: false\nerror:\n  code: not_authenticated\n", returncode=1),
    ):
        status, message = channel.check()
    assert status == "warn"
    assert "configure twitter-cookies" in message


def test_check_passes_config_credentials_into_status(tmp_path):
    from agent_reach.config import Config

    config = Config(config_path=tmp_path / "config.yaml")
    config.set("twitter_auth_token", "auth-token")
    config.set("twitter_ct0", "ct0-token")

    captured = {}
    channel = TwitterChannel()
    with patch(
        "os.environ",
        {},
    ), patch(
        "agent_reach.channels.twitter.find_command",
        return_value="/usr/local/bin/twitter",
    ), patch(
        "subprocess.run",
        side_effect=lambda *args, **kwargs: captured.update({"env": kwargs.get("env")}) or _cp(stdout="ok: true", returncode=0),
    ):
        status, _message = channel.check(config)

    assert status == "ok"
    assert captured["env"]["AUTH_TOKEN"] == "auth-token"
    assert captured["env"]["CT0"] == "ct0-token"
