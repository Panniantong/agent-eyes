# -*- coding: utf-8 -*-
"""Tests for doctor module."""

import pytest

from agent_reach.channels.exa_search import ExaSearchChannel
from agent_reach.config import Config
from agent_reach.doctor import check_all, format_report


@pytest.fixture
def tmp_config(tmp_path):
    return Config(config_path=tmp_path / "config.yaml")


class TestDoctor:
    def test_doctor_has_core_channels(self, tmp_config):
        results = check_all(tmp_config)
        assert "web" in results
        assert "github" in results
        assert "twitter" in results
        assert "exa_search" in results

    def test_each_result_has_required_fields(self, tmp_config):
        results = check_all(tmp_config)
        for item in results.values():
            assert "status" in item
            assert "name" in item
            assert "message" in item
            assert "signals" in item
            assert item["status"] in {"ok", "warn", "off", "error"}
            assert set(item["signals"]) == {"installed", "configured", "reachable", "authenticated"}
            assert set(item["signals"].values()) <= {"yes", "no", "unknown", "n/a"}

    def test_exa_channel_off_when_mcporter_missing(self, monkeypatch):
        import agent_reach.channels.exa_search as exa_mod
        monkeypatch.setattr(exa_mod.shutil, "which", lambda _: None)
        status, _ = ExaSearchChannel().check()
        assert status == "off"

    def test_exa_channel_ok_when_mcporter_has_exa(self, monkeypatch):
        import agent_reach.channels.exa_search as exa_mod
        monkeypatch.setattr(exa_mod.shutil, "which", lambda _: "mcporter")

        class Result:
            stdout = "exa"

        monkeypatch.setattr(exa_mod.subprocess, "run", lambda *args, **kwargs: Result())
        status, _ = ExaSearchChannel().check()
        assert status == "ok"

    def test_format_report(self, tmp_config):
        results = check_all(tmp_config)
        report = format_report(results)
        assert "Agent Reach" in report
        assert "✅" in report
        assert "渠道可用" in report
        assert "I=installed" in report
