"""
Data models for LogLens.

LogRecord: Normalized, structured log entry.
RawEvent: Raw event from a source before normalization.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LogRecord:
    """
    Normalized log record with minimal required fields.
    
    Fields:
        timestamp: ISO-8601 formatted timestamp string
        severity_num: Numeric severity (0-7, syslog/journald priority)
        severity_label: Human-readable severity label (e.g., "ERROR", "INFO")
        message: Log message content
        raw: Optional raw event data for advanced inspection
    """
    timestamp: str
    severity_num: int
    severity_label: str
    message: str
    raw: Optional[Dict[str, Any]] = field(default=None, repr=False)

    def __post_init__(self):
        """Validate severity_num is in valid range."""
        if not (0 <= self.severity_num <= 7):
            raise ValueError(f"severity_num must be 0-7, got {self.severity_num}")


@dataclass
class RawEvent:
    """
    Raw event from a log source before normalization.
    
    Fields:
        data: Raw event data (dict for structured sources, str for text sources)
        source_type: Type of source that produced this event (e.g., "journalctl", "file")
        metadata: Optional source-specific metadata
    """
    data: Any  # Dict for JSON sources, str for text sources
    source_type: str
    metadata: Optional[Dict[str, Any]] = None
