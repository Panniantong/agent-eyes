# -*- coding: utf-8 -*-
"""Tests for AgentReach core class."""

import pytest
from unittest.mock import patch, MagicMock
from agent_reach.config import Config
from agent_reach.core import AgentReach
from agent_reach.channels.base import ReadResult


@pytest.fixture
def eyes(tmp_path):
    config = Config(config_path=tmp_path / "config.yaml")
    return AgentReach(config=config)


class TestAgentReach:
    def test_init(self, eyes):
        assert eyes.config is not None

    def test_detect_platform(self, eyes):
        assert eyes.detect_platform("https://github.com/test/repo") == "github"
        assert eyes.detect_platform("https://reddit.com/r/test") == "reddit"
        assert eyes.detect_platform("https://x.com/user/status/123") == "twitter"
        assert eyes.detect_platform("https://youtube.com/watch?v=abc") == "youtube"
        assert eyes.detect_platform("https://bilibili.com/video/BV1xx") == "bilibili"
        assert eyes.detect_platform("https://example.com") == "web"

    def test_doctor(self, eyes):
        results = eyes.doctor()
        assert isinstance(results, dict)
        assert "web" in results
        assert "github" in results

    def test_doctor_report(self, eyes):
        report = eyes.doctor_report()
        assert isinstance(report, str)
        assert "Agent Reach" in report

    @patch("agent_reach.channels.web.WebChannel.read")
    @pytest.mark.asyncio
    async def test_read_batch(self, mock_read, eyes):
        mock_read.return_value = ReadResult(
            title="T", content="C", url="https://example.com", platform="web"
        )
        results = await eyes.read_batch(["https://example.com", "https://example.org"])
        assert len(results) == 2
