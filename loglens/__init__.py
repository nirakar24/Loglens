"""
LogLens - A Linux log processing engine with pluggable sources.

Phase 1: Backend - log fetching, normalization, and filtering.
Phase 2: TUI - Textual-based log viewer (requires textual package).
"""

from .engine import fetch_logs, filter_logs, get_diagnostics, reset_diagnostics
from .model import LogRecord, RawEvent

__version__ = "0.2.0"
__all__ = [
    "fetch_logs",
    "filter_logs",
    "get_diagnostics",
    "reset_diagnostics",
    "LogRecord",
    "RawEvent",
]

# Optional TUI import (requires textual)
try:
    from .tui.app import run_tui
    __all__.append("run_tui")
except ImportError:
    # textual not installed
    pass
