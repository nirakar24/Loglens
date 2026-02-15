"""
LogLens - A Linux log processing engine with pluggable sources.

Phase 1: Backend-only log fetching, normalization, and filtering.
"""

from .engine import fetch_logs, filter_logs, get_diagnostics, reset_diagnostics
from .model import LogRecord, RawEvent

__version__ = "0.1.0"
__all__ = [
    "fetch_logs",
    "filter_logs",
    "get_diagnostics",
    "reset_diagnostics",
    "LogRecord",
    "RawEvent",
]
