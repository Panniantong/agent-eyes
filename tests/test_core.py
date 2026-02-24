# -*- coding: utf-8 -*-
"""Tests for AgentEyes core class."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from agent_eyes.config import Config
from agent_eyes.core import AgentEyes


@pytest.fixture
def eyes(tmp_path):
    config = Config(config_path=tmp_path / "config.yaml")
    return AgentEyes(config=config)


class TestAgentEyes:
    def test_init(self, eyes):
        assert eyes.config is not None
        assert eyes.reader is not None

    def test_detect_platform(self, eyes):
        assert eyes.detect_platform("https://github.com/openai/gpt-4") == "github"
        assert eyes.detect_platform("https://reddit.com/r/test") == "reddit"
        assert eyes.detect_platform("https://x.com/elonmusk/status/123") == "twitter"
        assert eyes.detect_platform("https://youtube.com/watch?v=abc") == "youtube"
        assert eyes.detect_platform("https://bilibili.com/video/BV1xx") == "bilibili"
        assert eyes.detect_platform("https://mp.weixin.qq.com/s/abc") == "wechat"
        assert eyes.detect_platform("https://example.com") == "generic"

    def test_doctor(self, eyes):
        results = eyes.doctor()
        assert isinstance(results, dict)
        assert "web" in results
        assert "github_read" in results

    def test_doctor_report(self, eyes):
        report = eyes.doctor_report()
        assert isinstance(report, str)
        assert "Agent Eyes" in report
