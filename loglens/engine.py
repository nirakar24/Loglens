"""
Main engine API for LogLens.

Public interface for fetching and filtering logs.
"""

from typing import Any, Iterator, Optional, Union, Dict

from .model import LogRecord
from .normalize import normalize_event, get_normalization_stats, reset_normalization_stats
from .filtering import filter_logs as apply_filters
from .sources import get_source, LogSource
from .sources.registry import register_source
from .sources.journalctl import JournalctlSource
from .sources.file import FileSource


# Register built-in sources
register_source("journalctl", JournalctlSource)
register_source("file", FileSource)


def fetch_logs(
    source: Union[str, LogSource] = "journalctl",
    *,
    limit: Optional[int] = None,
    warn_on_errors: bool = False,
    **source_kwargs: Any,
) -> Iterator[LogRecord]:
    """
    Fetch logs from a source and return normalized LogRecord objects.
    
    This is the main entry point for fetching logs. It handles:
    1. Initializing the log source (by name or instance)
    2. Reading raw events from the source
    3. Normalizing events into LogRecord objects
    
    Args:
        source: Source name (e.g., "journalctl", "file") or LogSource instance
        limit: Maximum number of records to return (None = unlimited)
        warn_on_errors: If True, print warnings for data quality issues to stderr
        **source_kwargs: Arguments passed to source constructor if source is a string
                        (e.g., since, until, units, priority for journalctl;
                         path, mode, encoding for file)
        
    Yields:
        LogRecord objects
        
    Raises:
        KeyError: If source name is not registered
        SourceError: If source cannot be read
        NormalizationError: If events cannot be normalized
        
    Examples:
        # Fetch from journalctl (default, last 24 hours)
        >>> for record in fetch_logs():
        ...     print(record.message)
        
        # Fetch limited number of records with warnings
        >>> for record in fetch_logs(limit=100, warn_on_errors=True):
        ...     print(record.message)
        
        # Fetch from journalctl with custom time range
        >>> for record in fetch_logs("journalctl", since="2026-02-14 00:00:00"):
        ...     print(record.message)
        
        # Fetch from a file
        >>> for record in fetch_logs("file", path="/var/log/app.log", mode="text"):
        ...     print(record.message)
    """
    # Add warn_on_errors to source_kwargs if it's a recognized parameter
    if isinstance(source, str) and source == "journalctl":
        source_kwargs.setdefault("warn_on_errors", warn_on_errors)
    
    # Resolve source
    if isinstance(source, str):
        source_instance = get_source(source, **source_kwargs)
    else:
        source_instance = source
    
    # Read and normalize events
    count = 0
    with source_instance:
        for raw_event in source_instance.read():
            yield normalize_event(raw_event, warn_on_missing=warn_on_errors)
            count += 1
            if limit is not None and count >= limit:
                break


def filter_logs(
    records: Iterator[LogRecord],
    *,
    severity: Optional[Union[str, int]] = None,
    min_severity: Optional[Union[str, int]] = None,
    keyword: Optional[str] = None,
    case_sensitive: bool = False,
) -> Iterator[LogRecord]:
    """
    Filter log records based on criteria.
    
    All filters are applied with AND logic (record must match all criteria).
    
    Args:
        records: Iterator of LogRecord objects to filter
        severity: Exact severity match (label or number). Mutually exclusive with min_severity.
        min_severity: Minimum severity threshold (label or number). Records at this level
                      or more severe (lower number) are included.
        keyword: Substring to search for in message. Case-insensitive by default.
        case_sensitive: If True, keyword search is case-sensitive. Default False.
        
    Yields:
        LogRecord objects that match all filters
        
    Raises:
        ValueError: If both severity and min_severity are specified
        
    Examples:
        # Fetch and filter by minimum severity
        >>> logs = fetch_logs()
        >>> for record in filter_logs(logs, min_severity="warning"):
        ...     print(f"{record.severity_label}: {record.message}")
        
        # Fetch and filter by exact severity + keyword
        >>> logs = fetch_logs()
        >>> for record in filter_logs(logs, severity="error", keyword="failed"):
        ...     print(record.message)
    """
    return apply_filters(
        records,
        severity=severity,
        min_severity=min_severity,
        keyword=keyword,
        case_sensitive=case_sensitive,
    )


def fetch_and_filter_logs(
    source: Union[str, LogSource] = "journalctl",
    *,
    severity: Optional[Union[str, int]] = None,
    min_severity: Optional[Union[str, int]] = None,
    keyword: Optional[str] = None,
    case_sensitive: bool = False,
    limit: Optional[int] = None,
    warn_on_errors: bool = False,
    **source_kwargs: Any,
) -> Iterator[LogRecord]:
    """
    Convenience function to fetch and filter logs in one call.
    
    Combines fetch_logs() and filter_logs() for simpler usage.
    
    Args:
        source: Source name or LogSource instance
        severity: Exact severity match
        min_severity: Minimum severity threshold
        keyword: Keyword to search for in messages
        case_sensitive: Case-sensitive keyword search
        limit: Maximum number of records to return (applied after filtering)
        warn_on_errors: If True, print warnings for data quality issues
        **source_kwargs: Arguments passed to source constructor
                        (e.g., since, until, units for journalctl)
        
    Yields:
        Filtered LogRecord objects
        
    Examples:
        # Fetch errors from journalctl in last 24 hours
        >>> for record in fetch_and_filter_logs(min_severity="error"):
        ...     print(f"{record.timestamp}: {record.message}")
        
        # Fetch from specific unit with keyword filter, limited to 100 records
        >>> for record in fetch_and_filter_logs(
        ...     units=["nginx.service"],
        ...     keyword="404",
        ...     limit=100,
        ... ):
        ...     print(record.message)
    """
    logs = fetch_logs(source, limit=limit, warn_on_errors=warn_on_errors, **source_kwargs)
    return filter_logs(
        logs,
        severity=severity,
        min_severity=min_severity,
        keyword=keyword,
        case_sensitive=case_sensitive,
    )


def get_diagnostics() -> Dict[str, Any]:
    """
    Get diagnostics information about log processing.
    
    Returns statistics about normalization and source reading,
    useful for debugging count mismatches and data quality issues.
    
    Returns:
        Dictionary with diagnostic information:
        - normalization: Stats from normalize layer (missing fields, etc.)
    
    Example:
        >>> list(fetch_logs(warn_on_errors=True))  # Consume iterator
        >>> diag = get_diagnostics()
        >>> print(f"Missing priority: {diag['normalization']['missing_priority']}")
    """
    return {
        "normalization": get_normalization_stats(),
    }


def reset_diagnostics() -> None:
    """
    Reset diagnostic counters.
    
    Useful when running multiple test batches.
    """
    reset_normalization_stats()
