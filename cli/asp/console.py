"""Shared Rich console configured for cross-platform Unicode safety."""

from __future__ import annotations

import sys
from rich.console import Console

# Reconfigure stdout/stderr to UTF-8 on Windows to avoid cp1252 charmap encoding errors
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console()
