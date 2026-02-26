# -*- coding: utf-8 -*-
"""Tests for doctor module."""

import pytest
from agent_reach.config import Config
from agent_reach.doctor import check_all, format_report


@pytest.fixture
def tmp_config(tmp_path):
    return Config(config_path=tmp_path / "config.yaml")


class TestDoctor:
    def test_zero_config_channels_ok(self, tmp_config):
        results = check_all(tmp_config)
        assert results["web"]["status"] == "ok"
        assert results["github"]["status"] in ("ok", "warn")  # warn if gh CLI not installed
        assert results["bilibili"]["status"] in ("ok", "warn")  # warn on servers
        assert results["rss"]["status"] == "ok"

    def test_exa_off_without_key(self, tmp_config):
        results = check_all(tmp_config)
        assert results["exa_search"]["status"] == "off"

    def test_exa_off_without_mcporter(self, tmp_config):
        """Exa now uses mcporter — api key alone is not enough."""
        tmp_config.set("exa_api_key", "test-key")
        results = check_all(tmp_config)
        # Without mcporter installed, should still be off
        assert results["exa_search"]["status"] == "off"

    def test_format_report(self, tmp_config):
        results = check_all(tmp_config)
        report = format_report(results)
        assert "Agent Reach" in report
        assert "✅" in report
        assert "渠道可用" in report

    def test_doctor_channel_crash_isolated(self, tmp_config):
        """单个 channel.check() 崩溃不应导致 check_all 失败"""
        from unittest.mock import patch
        with patch("agent_reach.channels.github.GitHubChannel.check", side_effect=RuntimeError("crash")):
            results = check_all(tmp_config)
            assert results["github"]["status"] == "error"
            assert "crash" in results["github"]["message"]
