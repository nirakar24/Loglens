"""
Filtering logic for log records.

Supports filtering by severity (exact or threshold) and keyword search.
"""

from typing import Iterator, Optional, Union

from .model import LogRecord
from .severity import label_to_priority, is_at_least_severity


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
    """
    if severity is not None and min_severity is not None:
        raise ValueError("Cannot specify both 'severity' and 'min_severity'")
    
    # Normalize severity filters
    exact_priority: Optional[int] = None
    min_priority: Optional[int] = None
    
    if severity is not None:
        exact_priority = label_to_priority(severity)
    
    if min_severity is not None:
        min_priority = label_to_priority(min_severity)
    
    # Process records
    for record in records:
        # Apply severity filter
        if exact_priority is not None:
            if record.severity_num != exact_priority:
                continue
        
        if min_priority is not None:
            if not is_at_least_severity(record.severity_num, min_priority):
                continue
        
        # Apply keyword filter
        if keyword is not None:
            if case_sensitive:
                if keyword not in record.message:
                    continue
            else:
                if keyword.lower() not in record.message.lower():
                    continue
        
        yield record


def filter_by_severity_exact(
    records: Iterator[LogRecord],
    severity: Union[str, int],
) -> Iterator[LogRecord]:
    """
    Filter records by exact severity match.
    
    Args:
        records: Iterator of LogRecord objects
        severity: Exact severity level (label or number)
        
    Yields:
        Records with matching severity
    """
    return filter_logs(records, severity=severity)


def filter_by_min_severity(
    records: Iterator[LogRecord],
    min_severity: Union[str, int],
) -> Iterator[LogRecord]:
    """
    Filter records by minimum severity threshold.
    
    Includes records at or above the severity level (lower or equal priority number).
    
    Args:
        records: Iterator of LogRecord objects
        min_severity: Minimum severity threshold (label or number)
        
    Yields:
        Records at or above severity threshold
    """
    return filter_logs(records, min_severity=min_severity)


def filter_by_keyword(
    records: Iterator[LogRecord],
    keyword: str,
    case_sensitive: bool = False,
) -> Iterator[LogRecord]:
    """
    Filter records by keyword search in message.
    
    Args:
        records: Iterator of LogRecord objects
        keyword: Substring to search for
        case_sensitive: If True, search is case-sensitive. Default False.
        
    Yields:
        Records containing the keyword
    """
    return filter_logs(records, keyword=keyword, case_sensitive=case_sensitive)
