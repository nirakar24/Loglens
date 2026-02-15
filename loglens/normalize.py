"""
Normalization layer to convert raw events into LogRecord objects.

Each source type may need its own normalization logic.
"""

import sys
from datetime import datetime
from typing import Dict, Any

from .model import RawEvent, LogRecord
from .severity import priority_to_label


# Global statistics for normalization
_normalization_stats = {
    "total": 0,
    "missing_priority": 0,
    "invalid_priority": 0,
    "missing_timestamp": 0,
    "missing_message": 0,
}


def get_normalization_stats() -> Dict[str, int]:
    """Get normalization statistics."""
    return _normalization_stats.copy()


def reset_normalization_stats() -> None:
    """Reset normalization statistics."""
    global _normalization_stats
    _normalization_stats = {
        "total": 0,
        "missing_priority": 0,
        "invalid_priority": 0,
        "missing_timestamp": 0,
        "missing_message": 0,
    }


class NormalizationError(Exception):
    """Raised when an event cannot be normalized."""
    pass


def normalize_event(event: RawEvent, warn_on_missing: bool = False) -> LogRecord:
    """
    Normalize a raw event into a LogRecord.
    
    Dispatches to appropriate normalizer based on source_type.
    
    Args:
        event: Raw event from a log source
        warn_on_missing: If True, print warnings for missing fields
        
    Returns:
        Normalized LogRecord
        
    Raises:
        NormalizationError: If event cannot be normalized
    """
    _normalization_stats["total"] += 1
    
    if event.source_type == "journalctl":
        return _normalize_journalctl(event, warn_on_missing)
    elif event.source_type == "file_jsonl":
        return _normalize_file_jsonl(event, warn_on_missing)
    elif event.source_type == "file_text":
        return _normalize_file_text(event, warn_on_missing)
    else:
        raise NormalizationError(f"Unknown source type: {event.source_type}")


def _normalize_journalctl(event: RawEvent, warn_on_missing: bool = False) -> LogRecord:
    """
    Normalize a journalctl JSON event.
    
    Journalctl fields (common):
        MESSAGE: Log message
        PRIORITY: Numeric priority (0-7)
        _SOURCE_REALTIME_TIMESTAMP: Microseconds since epoch
        __REALTIME_TIMESTAMP: Alternative timestamp field
        _SYSTEMD_UNIT: Systemd unit name
        SYSLOG_IDENTIFIER: Syslog identifier
    """
    if not isinstance(event.data, dict):
        raise NormalizationError("Journalctl event data must be a dict")
    
    data: Dict[str, Any] = event.data
    
    # Extract message
    message = data.get("MESSAGE", "")
    if not message:
        _normalization_stats["missing_message"] += 1
        if warn_on_missing:
            print(f"Warning: Event missing MESSAGE field", file=sys.stderr)
    if not isinstance(message, str):
        message = str(message)
    
    # Extract priority with better error handling
    severity_num = 6  # Default to INFO
    priority_field = data.get("PRIORITY")
    
    if priority_field is None:
        _normalization_stats["missing_priority"] += 1
        if warn_on_missing:
            print(f"Warning: Event missing PRIORITY field, defaulting to INFO", file=sys.stderr)
    else:
        try:
            severity_num = int(priority_field)
            if not (0 <= severity_num <= 7):
                _normalization_stats["invalid_priority"] += 1
                if warn_on_missing:
                    print(f"Warning: Invalid priority {severity_num}, defaulting to INFO", file=sys.stderr)
                severity_num = 6  # Default to INFO
        except (ValueError, TypeError):
            _normalization_stats["invalid_priority"] += 1
            if warn_on_missing:
                print(f"Warning: Non-numeric priority '{priority_field}', defaulting to INFO", file=sys.stderr)
            severity_num = 6  # Default to INFO
    
    severity_label = priority_to_label(severity_num)
    
    # Extract timestamp (prefer _SOURCE_REALTIME_TIMESTAMP)
    timestamp = _extract_journald_timestamp(data, warn_on_missing)
    
    return LogRecord(
        timestamp=timestamp,
        severity_num=severity_num,
        severity_label=severity_label,
        message=message,
        raw=data,
    )


def _extract_journald_timestamp(data: Dict[str, Any], warn_on_missing: bool = False) -> str:
    """
    Extract and format timestamp from journald event.
    
    Tries multiple timestamp fields in order of preference.
    Returns ISO-8601 formatted string.
    """
    # Try _SOURCE_REALTIME_TIMESTAMP first (microseconds since epoch)
    timestamp_us = data.get("_SOURCE_REALTIME_TIMESTAMP")
    if timestamp_us is None:
        timestamp_us = data.get("__REALTIME_TIMESTAMP")
    
    if timestamp_us is not None:
        try:
            # Convert microseconds to seconds
            timestamp_s = int(timestamp_us) / 1_000_000
            dt = datetime.fromtimestamp(timestamp_s)
            return dt.isoformat()
        except (ValueError, TypeError, OSError):
            pass
    
    # Fallback: use current time
    _normalization_stats["missing_timestamp"] += 1
    if warn_on_missing:
        print(f"Warning: Event missing valid timestamp, using current time", file=sys.stderr)
    return datetime.now().isoformat()


def _normalize_file_jsonl(event: RawEvent, warn_on_missing: bool = False) -> LogRecord:
    """
    Normalize a JSON Lines file event.
    
    This is a skeleton implementation. Real JSONL logs (e.g., Docker)
    have varying schemas. Future work: add parser plugins.
    
    Expected minimal schema:
        timestamp (optional): ISO-8601 or Unix timestamp
        message or msg: Log message
        level or severity: Severity label or number
    """
    if not isinstance(event.data, dict):
        raise NormalizationError("JSONL event data must be a dict")
    
    data: Dict[str, Any] = event.data
    
    # Extract message (try common field names)
    message = data.get("message") or data.get("msg") or data.get("log") or ""
    if not isinstance(message, str):
        message = str(message)
    
    # Extract severity (default to INFO if missing/unknown)
    severity_num = 6  # Default INFO
    severity_label = "INFO"
    
    level = data.get("level") or data.get("severity")
    if level is not None:
        try:
            # Try parsing as number
            if isinstance(level, int):
                severity_num = level if 0 <= level <= 7 else 6
            elif isinstance(level, str):
                # Common label mappings
                level_map = {
                    "debug": 7, "info": 6, "notice": 5, "warn": 4, "warning": 4,
                    "error": 3, "err": 3, "crit": 2, "critical": 2, "alert": 1, "emerg": 0
                }
                severity_num = level_map.get(level.lower(), 6)
            severity_label = priority_to_label(severity_num)
        except (ValueError, KeyError):
            pass
    
    # Extract timestamp
    timestamp_str = data.get("timestamp") or data.get("time") or data.get("@timestamp")
    if timestamp_str:
        try:
            # Try parsing as ISO-8601
            dt = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))
            timestamp = dt.isoformat()
        except (ValueError, TypeError):
            # Try parsing as Unix timestamp
            try:
                dt = datetime.fromtimestamp(float(timestamp_str))
                timestamp = dt.isoformat()
            except (ValueError, TypeError, OSError):
                timestamp = datetime.now().isoformat()
    else:
        timestamp = datetime.now().isoformat()
    
    return LogRecord(
        timestamp=timestamp,
        severity_num=severity_num,
        severity_label=severity_label,
        message=message,
        raw=data,
    )


def _normalize_file_text(event: RawEvent, warn_on_missing: bool = False) -> LogRecord:
    """
    Normalize a plain text line event.
    
    This is a basic implementation that treats each line as a message.
    Future work: add regex parsers for common formats (nginx, syslog, etc.).
    """
    if not isinstance(event.data, str):
        raise NormalizationError("Text file event data must be a string")
    
    # Basic implementation: entire line is the message
    # Default to INFO severity, current time
    message = event.data
    severity_num = 6
    severity_label = "INFO"
    timestamp = datetime.now().isoformat()
    
    return LogRecord(
        timestamp=timestamp,
        severity_num=severity_num,
        severity_label=severity_label,
        message=message,
        raw={"line": message},
    )
