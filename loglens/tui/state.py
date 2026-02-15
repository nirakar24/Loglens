"""
UI state management for LogLens TUI.

Contains state models for filter criteria, application state, and UI configuration.
NO backend logic - pure data structures only.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from loglens.model import LogRecord


@dataclass
class FilterState:
    """Represents current filter criteria."""
    severity: Optional[str] = None  # Exact severity match
    min_severity: Optional[str] = None  # Minimum severity threshold
    keyword: Optional[str] = None  # Text search
    case_sensitive: bool = False
    category: Optional[str] = None  # Sidebar category filter (systemd unit/app)


@dataclass
class AppState:
    """Application-wide state."""
    filters: FilterState = field(default_factory=FilterState)
    follow_mode: bool = False  # Only for journalctl
    selected_category: Optional[str] = None
    selected_log_index: Optional[int] = None
    show_raw_details: bool = False  # Toggle between curated and raw view
    records: List[LogRecord] = field(default_factory=list)  # In-memory buffer
    error_message: Optional[str] = None
    status_message: str = "Press Ctrl+Q to quit"
    
    def reset_records(self):
        """Clear the in-memory buffer."""
        self.records.clear()
        self.selected_log_index = None
    
    def apply_filters(self) -> List[LogRecord]:
        """Apply current filters to in-memory records."""
        filtered = self.records
        
        # Category filter
        if self.filters.category:
            filtered = [r for r in filtered if self._get_category(r) == self.filters.category]
        
        # Severity filter (handled by filter_logs in backend)
        # Keyword filter (handled by filter_logs in backend)

        # Always show newest first
        return sorted(filtered, key=self._timestamp_sort_key, reverse=True)

    def _timestamp_sort_key(self, record: LogRecord) -> tuple:
        """Sort key for timestamps (handles missing/invalid values safely)."""
        ts = record.timestamp
        if not ts:
            return (0.0, "")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return (dt.timestamp(), ts)
            except Exception:
                return (0.0, ts)
        try:
            return (float(ts), str(ts))
        except Exception:
            return (0.0, str(ts))
    
    def _get_category(self, record: LogRecord) -> str:
        """Extract category from LogRecord.raw."""
        if not record.raw:
            return "(unknown)"
        
        # Priority order: _SYSTEMD_UNIT → SYSLOG_IDENTIFIER
        unit = record.raw.get('_SYSTEMD_UNIT', '').strip()
        if unit:
            return unit
        
        syslog_id = record.raw.get('SYSLOG_IDENTIFIER', '').strip()
        if syslog_id:
            return syslog_id
        
        return "(unknown)"
    
    def get_categories(self) -> List[str]:
        """Extract unique categories from current records."""
        categories = set()
        for record in self.records:
            categories.add(self._get_category(record))
        return sorted(categories)
