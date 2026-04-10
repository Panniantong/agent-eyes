# -*- coding: utf-8 -*-
"""Tests for the Windows/Codex CLI surface."""

import json
from unittest.mock import patch

import agent_reach.cli as cli
from agent_reach.cli import main


class TestCLI:
    def test_version(self, capsys):
        assert main(["version"]) == 0
        assert "Agent Reach v" in capsys.readouterr().out

    def test_no_command_shows_help(self):
        assert main([]) == 0

    def test_parse_twitter_cookie_input_separate_values(self):
        auth_token, ct0 = cli._parse_twitter_cookie_input("token123 ct0abc")
        assert auth_token == "token123"
        assert ct0 == "ct0abc"

    def test_parse_twitter_cookie_input_cookie_header(self):
        auth_token, ct0 = cli._parse_twitter_cookie_input(
            "auth_token=token123; ct0=ct0abc; other=value"
        )
        assert auth_token == "token123"
        assert ct0 == "ct0abc"

    def test_safe_install_lists_windows_commands(self, capsys, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _name: None)
        monkeypatch.setattr("agent_reach.cli.find_command", lambda _name: None)
        with patch("agent_reach.cli.render_ytdlp_fix_command", return_value="FIX-YTDLP"):
            assert main(["install", "--safe", "--channels=twitter"]) == 0
        output = capsys.readouterr().out
        assert "GitHub.cli" in output
        assert "yt-dlp.yt-dlp" in output
        assert "npm install -g mcporter" in output
        assert ".mcporter\\mcporter.json" in output
        assert "uv tool install twitter-cli" in output
        assert "FIX-YTDLP" in output

    def test_install_dry_run_json(self, capsys, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _name: None)
        monkeypatch.setattr("agent_reach.cli.find_command", lambda _name: None)
        with patch("agent_reach.cli.render_ytdlp_fix_command", return_value="FIX-YTDLP"):
            assert main(["install", "--dry-run", "--json", "--channels=twitter"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["command"] == "install"
        assert payload["mode"] == "dry-run"
        assert payload["optional_channels_requested"] == ["twitter"]
        assert "FIX-YTDLP" in payload["commands"]
        assert payload["execution_context"] == "checkout"
        assert payload["plugin_manifest"] is not None
        assert payload["mcp_config"] is not None

    def test_install_parses_all_as_twitter(self, monkeypatch):
        calls = []

        monkeypatch.setattr(cli, "_ensure_gh_cli", lambda: True)
        monkeypatch.setattr(cli, "_ensure_ytdlp", lambda: True)
        monkeypatch.setattr(cli, "_ensure_nodejs", lambda: True)
        monkeypatch.setattr(cli, "_ensure_mcporter", lambda: True)
        monkeypatch.setattr(cli, "_ensure_exa_config", lambda: True)
        monkeypatch.setattr(cli, "_ensure_ytdlp_js_runtime", lambda: True)
        monkeypatch.setattr(cli, "_install_skill", lambda: [])
        monkeypatch.setattr(cli, "_detect_environment", lambda: "local")
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr(
            cli,
            "_install_twitter_deps",
            lambda: calls.append("twitter") or True,
        )
        monkeypatch.setattr(
            "agent_reach.doctor.check_all",
            lambda _config: {
                "web": {
                    "status": "ok",
                    "name": "web",
                    "description": "Any web page",
                    "message": "ok",
                    "tier": 0,
                    "backends": [],
                }
            },
        )
        monkeypatch.setattr("agent_reach.doctor.format_report", lambda _results: "report")

        assert main(["install", "--channels=all"]) == 0
        assert calls == ["twitter"]

    def test_doctor_json(self, capsys, monkeypatch):
        monkeypatch.setattr(
            "agent_reach.doctor.check_all",
            lambda _config, probe=False: {
                "web": {
                    "name": "web",
                    "description": "Any web page",
                    "status": "ok",
                    "message": "ready",
                    "tier": 0,
                }
            },
        )
        monkeypatch.setattr("agent_reach.doctor.doctor_exit_code", lambda _results: 0)
        assert main(["doctor", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["summary"]["ready"] == 1
        assert payload["channels"][0]["name"] == "web"

    def test_collect_json_success(self, capsys, monkeypatch):
        class _FakeClient:
            def collect(self, channel, operation, value, limit=None):
                return {
                    "ok": True,
                    "channel": channel,
                    "operation": operation,
                    "items": [{"id": "1", "title": "Example", "url": value}],
                    "raw": {"limit": limit},
                    "meta": {"count": 1, "limit": limit},
                    "error": None,
                }

        monkeypatch.setattr("agent_reach.cli.AgentReachClient", _FakeClient)

        assert (
            main(
                [
                    "collect",
                    "--channel",
                    "github",
                    "--operation",
                    "read",
                    "--input",
                    "openai/openai-python",
                    "--json",
                ]
            )
            == 0
        )
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["channel"] == "github"
        assert payload["items"][0]["url"] == "openai/openai-python"

    def test_collect_unknown_channel_returns_exit_2(self, capsys, monkeypatch):
        class _FakeClient:
            def collect(self, channel, operation, value, limit=None):
                return {
                    "ok": False,
                    "channel": channel,
                    "operation": operation,
                    "items": [],
                    "raw": None,
                    "meta": {"input": value},
                    "error": {
                        "code": "unknown_channel",
                        "message": "Unknown channel",
                        "details": {},
                    },
                }

        monkeypatch.setattr("agent_reach.cli.AgentReachClient", _FakeClient)

        assert (
            main(
                [
                    "collect",
                    "--channel",
                    "nope",
                    "--operation",
                    "read",
                    "--input",
                    "value",
                ]
            )
            == 2
        )
        output = capsys.readouterr().out
        assert "unknown_channel" in output

    def test_collect_read_with_limit_stays_json_safe(self, capsys, monkeypatch):
        class _FakeClient:
            def collect(self, channel, operation, value, limit=None):
                return {
                    "ok": True,
                    "channel": channel,
                    "operation": operation,
                    "items": [{"id": "1", "title": "Example", "url": value}],
                    "raw": None,
                    "meta": {"count": 1, "limit": limit},
                    "error": None,
                }

        monkeypatch.setattr("agent_reach.cli.AgentReachClient", _FakeClient)

        assert (
            main(
                [
                    "collect",
                    "--channel",
                    "web",
                    "--operation",
                    "read",
                    "--input",
                    "https://example.com",
                    "--limit",
                    "1",
                    "--json",
                ]
            )
            == 0
        )
        payload = json.loads(capsys.readouterr().out)
        assert payload["meta"]["limit"] == 1

    def test_parser_does_not_expose_watch_command(self):
        parser = cli._build_parser()
        help_text = parser.format_help()
        assert "watch" not in help_text

    def test_channels_json(self, capsys):
        assert main(["channels", "github", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["channel"]["name"] == "github"
        assert payload["channel"]["entrypoint_kind"] == "cli"

    def test_export_integration_json(self, capsys):
        assert main(["export-integration", "--client", "codex", "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["client"] == "codex"
        assert payload["execution_context"] == "checkout"
        assert payload["mcp_snippet"]["mcpServers"]["exa"]["url"] == "https://mcp.exa.ai/mcp"
        assert payload["python_sdk"]["availability"] == "project_env_only"

    def test_check_update_json(self, capsys, monkeypatch):
        monkeypatch.setattr(
            cli,
            "_build_update_payload",
            lambda: {
                "schema_version": "2026-04-10",
                "generated_at": "2026-04-10T00:00:00Z",
                "command": "check-update",
                "current_version": "1.4.0",
                "upstream_repo": "Panniantong/Agent-Reach",
                "status": "up_to_date",
                "latest_version": "1.4.0",
            },
        )
        assert main(["check-update", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "up_to_date"


class TestCheckUpdateRetry:
    def test_retry_timeout_classification(self):
        sleeps = []
        requests = cli._import_requests()

        with patch("requests.get", side_effect=requests.exceptions.Timeout("timed out")):
            resp, err, attempts = cli._github_get_with_retry(
                "https://api.github.com/test",
                timeout=1,
                retries=3,
                sleeper=lambda seconds: sleeps.append(seconds),
            )

        assert resp is None
        assert err == "timeout"
        assert attempts == 3
        assert sleeps == [1, 2]

    def test_retry_dns_classification(self):
        requests = cli._import_requests()
        error = requests.exceptions.ConnectionError("getaddrinfo failed for api.github.com")
        with patch("requests.get", side_effect=error):
            resp, err, attempts = cli._github_get_with_retry(
                "https://api.github.com/test",
                retries=1,
                sleeper=lambda _seconds: None,
            )
        assert resp is None
        assert err == "dns"
        assert attempts == 1

    def test_retry_rate_limit_then_success(self):
        sleeps = []

        class Response:
            def __init__(self, code, payload=None, headers=None):
                self.status_code = code
                self._payload = payload or {}
                self.headers = headers or {}

            def json(self):
                return self._payload

        sequence = [
            Response(429, headers={"Retry-After": "3"}),
            Response(200, payload={"tag_name": "v1.4.0"}),
        ]

        with patch("requests.get", side_effect=sequence):
            resp, err, attempts = cli._github_get_with_retry(
                "https://api.github.com/test",
                retries=3,
                sleeper=lambda seconds: sleeps.append(seconds),
            )

        assert err is None
        assert resp is not None
        assert resp.status_code == 200
        assert attempts == 2
        assert sleeps == [3.0]

    def test_classify_rate_limit_from_403(self):
        class Response:
            status_code = 403
            headers = {"X-RateLimit-Remaining": "0"}

            @staticmethod
            def json():
                return {"message": "API rate limit exceeded"}

        assert cli._classify_github_response_error(Response()) == "rate_limit"
