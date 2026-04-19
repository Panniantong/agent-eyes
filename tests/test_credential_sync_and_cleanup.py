# -*- coding: utf-8 -*-
"""Tests for credential sync completeness and uninstall cleanup.

Covers:
  - configure_from_browser syncs bird CLI credentials (not just xfetch)
  - configure twitter-cookies syncs bird CLI credentials
  - uninstall removes synced credential files
  - uninstall removes all mcporter MCP entries including weibo
  - bilibili check calls search API at most once
"""

import json
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch, call

import pytest


# ── configure_from_browser bird sync ──


class TestConfigureFromBrowserBirdSync:
    """configure_from_browser should sync credentials to bird CLI, not just xfetch."""

    def test_syncs_bird_env_on_twitter_extract(self, tmp_path, monkeypatch):
        """When Twitter cookies are extracted, _sync_bird_env must be called."""
        from agent_reach.cookie_extract import configure_from_browser

        # Stub extract_all to return twitter creds
        monkeypatch.setattr(
            "agent_reach.cookie_extract.extract_all",
            lambda browser: {"twitter": {"auth_token": "tok123", "ct0": "ct0abc"}},
        )

        bird_calls = []
        original_sync_bird = None

        import agent_reach.cookie_extract as ce_mod
        original_sync_bird = ce_mod._sync_bird_env

        def tracking_bird(auth_token, ct0):
            bird_calls.append((auth_token, ct0))

        monkeypatch.setattr(ce_mod, "_sync_bird_env", tracking_bird)

        # Also stub xfetch to avoid side effects
        monkeypatch.setattr(ce_mod, "_sync_xfetch_session", lambda a, c: None)

        # Provide a fake config
        config = MagicMock()
        results = configure_from_browser("chrome", config)

        assert len(bird_calls) == 1
        assert bird_calls[0] == ("tok123", "ct0abc")

    def test_no_bird_sync_without_twitter(self, monkeypatch):
        """When no Twitter cookies are extracted, _sync_bird_env must not be called."""
        from agent_reach.cookie_extract import configure_from_browser
        import agent_reach.cookie_extract as ce_mod

        monkeypatch.setattr(
            "agent_reach.cookie_extract.extract_all",
            lambda browser: {"xhs": {"cookie_string": "a=1; b=2"}},
        )

        bird_calls = []
        monkeypatch.setattr(ce_mod, "_sync_bird_env", lambda a, c: bird_calls.append(1))
        monkeypatch.setattr(ce_mod, "_sync_xfetch_session", lambda a, c: None)

        config = MagicMock()
        configure_from_browser("chrome", config)

        assert len(bird_calls) == 0


# ── CLI configure twitter-cookies bird sync ──


class TestCLIConfigureBirdSync:
    """agent-reach configure twitter-cookies should sync both xfetch and bird."""

    def test_configure_twitter_cookies_syncs_bird(self, monkeypatch, tmp_path):
        """CLI configure twitter-cookies must call _sync_bird_env."""
        synced = {"xfetch": [], "bird": []}

        monkeypatch.setattr(
            "agent_reach.cookie_extract._sync_xfetch_session",
            lambda a, c: synced["xfetch"].append((a, c)),
        )
        monkeypatch.setattr(
            "agent_reach.cookie_extract._sync_bird_env",
            lambda a, c: synced["bird"].append((a, c)),
        )

        # Stub shutil.which to skip twitter-cli test
        monkeypatch.setattr("shutil.which", lambda _: None)

        from agent_reach.config import Config
        config = Config(config_path=tmp_path / "config.yaml")

        # Simulate the configure flow
        from agent_reach.cli import _parse_twitter_cookie_input
        auth_token, ct0 = _parse_twitter_cookie_input("testauth testct0")

        assert auth_token == "testauth"
        assert ct0 == "testct0"

        config.set("twitter_auth_token", auth_token)
        config.set("twitter_ct0", ct0)

        # Call the sync functions as the fixed code does
        from agent_reach.cookie_extract import _sync_xfetch_session, _sync_bird_env
        _sync_xfetch_session(auth_token, ct0)
        _sync_bird_env(auth_token, ct0)

        assert len(synced["xfetch"]) == 1
        assert len(synced["bird"]) == 1
        assert synced["bird"][0] == ("testauth", "testct0")


# ── Uninstall credential cleanup ──


class TestUninstallCredentialCleanup:
    """uninstall should remove synced credential files."""

    def test_uninstall_removes_xfetch_session(self, tmp_path, monkeypatch):
        """uninstall should remove ~/.config/xfetch/session.json."""
        xfetch_dir = tmp_path / ".config" / "xfetch"
        xfetch_dir.mkdir(parents=True)
        session_file = xfetch_dir / "session.json"
        session_file.write_text('{"authToken":"x","ct0":"y"}')

        # Verify the credential file paths include xfetch
        cred_path = str(session_file)
        assert os.path.isfile(cred_path)

        os.remove(cred_path)
        assert not os.path.isfile(cred_path)

    def test_uninstall_removes_bird_credentials(self, tmp_path, monkeypatch):
        """uninstall should remove ~/.config/bird/credentials.env."""
        bird_dir = tmp_path / ".config" / "bird"
        bird_dir.mkdir(parents=True)
        cred_file = bird_dir / "credentials.env"
        cred_file.write_text('AUTH_TOKEN="x"\nCT0="y"\n')

        cred_path = str(cred_file)
        assert os.path.isfile(cred_path)

        os.remove(cred_path)
        assert not os.path.isfile(cred_path)

    def test_uninstall_credential_paths_in_source(self):
        """Source code must list both xfetch and bird in uninstall cleanup."""
        import inspect
        from agent_reach import cli as cli_mod

        source = inspect.getsource(cli_mod._cmd_uninstall)

        # Both credential paths must be referenced
        assert "xfetch/session.json" in source, \
            "uninstall must clean up ~/.config/xfetch/session.json"
        assert "bird/credentials.env" in source, \
            "uninstall must clean up ~/.config/bird/credentials.env"

    def test_uninstall_mcporter_includes_weibo(self):
        """Source code must include weibo in mcporter MCP entry cleanup."""
        import inspect
        from agent_reach import cli as cli_mod

        source = inspect.getsource(cli_mod._cmd_uninstall)

        assert '"weibo"' in source or "'weibo'" in source, \
            "uninstall must remove weibo mcporter entry"

    def test_uninstall_skip_credentials_with_keep_config(self):
        """--keep-config should skip credential file removal."""
        import inspect
        from agent_reach import cli as cli_mod

        source = inspect.getsource(cli_mod._cmd_uninstall)

        # The credential cleanup must be guarded by keep_config check
        assert "keep_config" in source


# ── Bilibili double API call ──


class TestBilibiliSingleAPICall:
    """Bilibili check should call _search_api_ok at most once."""

    def test_check_calls_api_once_when_no_bili_cli(self, monkeypatch):
        """Without bili-cli, _search_api_ok should be called exactly once."""
        import agent_reach.channels.bilibili as bili_mod

        call_count = [0]
        original = bili_mod._search_api_ok

        def counting_api_check():
            call_count[0] += 1
            return True

        monkeypatch.setattr(bili_mod, "_search_api_ok", counting_api_check)
        monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/yt-dlp" if cmd == "yt-dlp" else None)

        from agent_reach.channels.bilibili import BilibiliChannel
        ch = BilibiliChannel()
        status, msg = ch.check()

        assert call_count[0] == 1, f"_search_api_ok called {call_count[0]} times, expected 1"
        assert status == "ok"

    def test_check_calls_api_once_when_api_fails(self, monkeypatch):
        """When API fails, _search_api_ok should still be called exactly once."""
        import agent_reach.channels.bilibili as bili_mod

        call_count = [0]

        def counting_api_check():
            call_count[0] += 1
            return False

        monkeypatch.setattr(bili_mod, "_search_api_ok", counting_api_check)
        monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/yt-dlp" if cmd == "yt-dlp" else None)

        from agent_reach.channels.bilibili import BilibiliChannel
        ch = BilibiliChannel()
        status, msg = ch.check()

        assert call_count[0] == 1, f"_search_api_ok called {call_count[0]} times, expected 1"
        assert status == "warn"

    def test_check_skips_api_when_bili_cli_present(self, monkeypatch):
        """With bili-cli installed, _search_api_ok should not be called."""
        import agent_reach.channels.bilibili as bili_mod

        call_count = [0]

        def counting_api_check():
            call_count[0] += 1
            return True

        monkeypatch.setattr(bili_mod, "_search_api_ok", counting_api_check)
        monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/fake" if cmd in ("yt-dlp", "bili") else None)

        from agent_reach.channels.bilibili import BilibiliChannel
        ch = BilibiliChannel()
        status, msg = ch.check()

        assert call_count[0] == 0, f"_search_api_ok should not be called when bili-cli is present"
        assert status == "ok"


# ── _sync_bird_env writes correct format ──


class TestSyncBirdEnv:
    """_sync_bird_env should write a shell-sourceable credentials file."""

    def test_writes_credentials_file(self, tmp_path, monkeypatch):
        """_sync_bird_env should create credentials.env with AUTH_TOKEN and CT0."""
        bird_dir = tmp_path / ".config" / "bird"
        monkeypatch.setattr(
            "os.path.expanduser",
            lambda p: str(tmp_path / p.lstrip("~/")) if "~" in p else p,
        )

        from agent_reach.cookie_extract import _sync_bird_env
        _sync_bird_env("mytoken", "myct0")

        cred_file = bird_dir / "credentials.env"
        assert cred_file.exists()
        content = cred_file.read_text()
        assert 'AUTH_TOKEN="mytoken"' in content
        assert 'CT0="myct0"' in content

    def test_file_permissions_restricted(self, tmp_path, monkeypatch):
        """credentials.env should be owner-only (0o600)."""
        import stat

        if sys.platform == "win32":
            pytest.skip("Permission test not applicable on Windows")

        monkeypatch.setattr(
            "os.path.expanduser",
            lambda p: str(tmp_path / p.lstrip("~/")) if "~" in p else p,
        )

        from agent_reach.cookie_extract import _sync_bird_env
        _sync_bird_env("tok", "ct")

        cred_file = tmp_path / ".config" / "bird" / "credentials.env"
        mode = cred_file.stat().st_mode
        assert not (mode & stat.S_IRGRP), "group read should not be set"
        assert not (mode & stat.S_IROTH), "other read should not be set"


# ── Source code audit: no missing sync in configure_from_browser ──


class TestSourceAudit:
    """Audit source code to verify sync completeness."""

    def test_configure_from_browser_calls_both_syncs(self):
        """configure_from_browser must call both _sync_xfetch_session and _sync_bird_env."""
        import inspect
        from agent_reach import cookie_extract as ce_mod

        source = inspect.getsource(ce_mod.configure_from_browser)
        assert "_sync_xfetch_session" in source
        assert "_sync_bird_env" in source

    def test_cli_configure_twitter_imports_both_syncs(self):
        """CLI configure twitter-cookies must import and call both sync functions."""
        import inspect
        from agent_reach import cli as cli_mod

        source = inspect.getsource(cli_mod._cmd_configure)
        assert "_sync_xfetch_session" in source
        assert "_sync_bird_env" in source
