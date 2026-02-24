# -*- coding: utf-8 -*-
"""Tests for Agent Eyes CLI."""

import pytest
from unittest.mock import patch
from agent_eyes.cli import main


class TestCLI:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["agent-eyes", "version"]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Agent Eyes v" in captured.out

    def test_no_command_shows_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["agent-eyes"]):
                main()
        assert exc_info.value.code == 0

    def test_doctor_runs(self, capsys):
        with patch("sys.argv", ["agent-eyes", "doctor"]):
            main()
        captured = capsys.readouterr()
        assert "Agent Eyes" in captured.out
        assert "✅" in captured.out
