# -*- coding: utf-8 -*-
"""Helpers for locating mcporter executable reliably across platforms."""

import shutil
from typing import Optional


def find_mcporter() -> Optional[str]:
    """Return absolute mcporter executable path if available."""
    return shutil.which("mcporter")

