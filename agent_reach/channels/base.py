# -*- coding: utf-8 -*-
"""Base types for supported research channels."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple


class Channel(ABC):
    """A research source that Agent Reach can diagnose for availability."""

    name: str = ""
    description: str = ""
    backends: List[str] = []
    tier: int = 0  # 0 = core, 1 = optional login/setup, 2 = advanced/manual
    auth_kind: str = "none"
    entrypoint_kind: str = "cli"
    operations: List[str] = []
    required_commands: List[str] = []
    host_patterns: List[str] = []
    example_invocations: List[str] = []
    supports_probe: bool = False
    install_hints: List[str] = []

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True when this channel is a natural fit for the URL."""

    def check(self, config=None) -> Tuple[str, str]:
        """Return a health tuple: (status, message)."""

        summary = ", ".join(self.backends) if self.backends else "configured"
        return "ok", summary

    def probe(self, config=None) -> Tuple[str, str]:
        """Run a lightweight live validation when supported."""

        return self.check(config)

    def to_contract(self) -> dict:
        """Return the machine-readable channel contract."""

        return {
            "name": self.name,
            "description": self.description,
            "tier": self.tier,
            "backends": list(self.backends),
            "auth_kind": self.auth_kind,
            "entrypoint_kind": self.entrypoint_kind,
            "operations": list(self.operations),
            "required_commands": list(self.required_commands),
            "host_patterns": list(self.host_patterns),
            "example_invocations": list(self.example_invocations),
            "supports_probe": self.supports_probe,
            "install_hints": list(self.install_hints),
        }
