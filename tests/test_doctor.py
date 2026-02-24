# -*- coding: utf-8 -*-
"""Tests for Agent Eyes doctor module."""

import pytest
from unittest.mock import patch, MagicMock

from agent_eyes.config import Config
from agent_eyes.doctor import check_all, format_report, STATUS_OK, STATUS_OFF


@pytest.fixture
def tmp_config(tmp_path):
    return Config(config_path=tmp_path / "config.yaml")


class TestDoctor:
    def test_zero_config_platforms_always_ok(self, tmp_config):
        results = check_all(tmp_config)
        assert results["web"]["status"] == STATUS_OK
        assert results["github_read"]["status"] == STATUS_OK
        assert results["bilibili"]["status"] == STATUS_OK
        assert results["rss"]["status"] == STATUS_OK
        assert results["tweet_read"]["status"] == STATUS_OK

    def test_search_off_without_exa_key(self, tmp_config):
        results = check_all(tmp_config)
        assert results["search_web"]["status"] == STATUS_OFF
        assert results["search_reddit"]["status"] == STATUS_OFF
        assert results["search_twitter"]["status"] == STATUS_OFF

    def test_search_on_with_exa_key(self, tmp_config):
        tmp_config.set("exa_api_key", "test-key")
        results = check_all(tmp_config)
        assert results["search_web"]["status"] == STATUS_OK
        assert results["search_reddit"]["status"] == STATUS_OK
        assert results["search_twitter"]["status"] == STATUS_OK

    def test_github_search_always_on(self, tmp_config):
        results = check_all(tmp_config)
        assert results["search_github"]["status"] == STATUS_OK

    def test_reddit_full_off_without_proxy(self, tmp_config):
        results = check_all(tmp_config)
        assert results["reddit_full"]["status"] == STATUS_OFF

    def test_reddit_full_on_with_proxy(self, tmp_config):
        tmp_config.set("reddit_proxy", "http://user:pass@ip:port")
        results = check_all(tmp_config)
        assert results["reddit_full"]["status"] == STATUS_OK

    @patch("agent_eyes.doctor._check_command")
    def test_birdx_detection(self, mock_cmd, tmp_config):
        mock_cmd.return_value = True
        results = check_all(tmp_config)
        assert results["twitter_advanced"]["status"] == STATUS_OK

    def test_format_report_is_string(self, tmp_config):
        results = check_all(tmp_config)
        report = format_report(results)
        assert isinstance(report, str)
        assert "Agent Eyes" in report
        assert "✅" in report

    def test_format_report_shows_count(self, tmp_config):
        results = check_all(tmp_config)
        report = format_report(results)
        assert "platforms active" in report
