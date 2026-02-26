# -*- coding: utf-8 -*-
"""Tests for Agent Reach CLI."""

import pytest
from unittest.mock import patch
from agent_reach.cli import main


class TestCLI:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["agent-reach", "version"]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Agent Reach v" in captured.out

    def test_no_command_shows_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["agent-reach"]):
                main()
        assert exc_info.value.code == 0

    def test_doctor_runs(self, capsys):
        with patch("sys.argv", ["agent-reach", "doctor"]):
            main()
        captured = capsys.readouterr()
        assert "Agent Reach" in captured.out
        assert "✅" in captured.out
