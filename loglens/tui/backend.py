"""
Backend adapter layer for LogLens TUI.

Provides a clean boundary between engine API (iterator-based) and UI needs (list-based).
All backend logic lives in loglens.engine - this module ONLY adapts/orchestrates.
"""

from typing import Iterator, Optional, List
from loglens import fetch_logs, filter_logs, get_diagnostics, reset_diagnostics
from loglens.model import LogRecord
from loglens.sources.base import SourceError


class BackendAdapter:
    """
    Adapter between engine API and UI needs.
    
    Handles:
    - Converting iterators to lists with limits
    - Applying filters via engine.filter_logs
    - Error handling and diagnostics
    """
    
    def __init__(self, max_buffer: Optional[int] = 10000):
        """
        Initialize adapter.
        
        Args:
            max_buffer: Maximum records to hold in memory (ring buffer cap).
                        If None, no cap is applied (use with care).
        """
        self.max_buffer = max_buffer
    
    def fetch_records(
        self,
        source: str = "journalctl",
        limit: Optional[int] = None,
        follow: bool = False,
        severity: Optional[str] = None,
        min_severity: Optional[str] = None,
        keyword: Optional[str] = None,
        case_sensitive: bool = False,
        warn_on_errors: bool = False,
        **source_kwargs
    ) -> List[LogRecord]:
        """
        Fetch and filter logs, returning a list.
        
        Args:
            source: Source type ('journalctl' or 'file')
            limit: Maximum records to fetch
            follow: Enable follow mode (journalctl only)
            severity: Exact severity match
            min_severity: Minimum severity threshold
            keyword: Text search
            case_sensitive: Case-sensitive keyword search
            warn_on_errors: Print warnings to stderr
            **source_kwargs: Passed to source constructor
        
        Returns:
            List of LogRecord objects
        
        Raises:
            SourceError: On source failures
        """
        # Apply buffer cap if configured
        if self.max_buffer is None:
            effective_limit = limit
        else:
            effective_limit = min(limit or self.max_buffer, self.max_buffer)
        
        # Add follow flag to source kwargs if specified
        if follow:
            source_kwargs['follow'] = True
        
        try:
            # Fetch from engine
            records_iter = fetch_logs(
                source=source,
                limit=effective_limit,
                warn_on_errors=warn_on_errors,
                **source_kwargs
            )
            
            # Filter via engine (if filters specified)
            if severity or min_severity or keyword:
                records_iter = filter_logs(
                    records_iter,
                    severity=severity,
                    min_severity=min_severity,
                    keyword=keyword,
                    case_sensitive=case_sensitive
                )
            
            # Materialize to list
            records = list(records_iter)
            
            return records
        
        except SourceError as e:
            raise  # Let caller handle
    
    def get_stats(self) -> dict:
        """Get current diagnostics from engine."""
        return get_diagnostics()
    
    def reset_stats(self):
        """Reset engine diagnostics."""
        reset_diagnostics()
