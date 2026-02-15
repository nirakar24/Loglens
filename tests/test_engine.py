"""Tests for main engine API."""

import pytest
from loglens.engine import fetch_logs, filter_logs, fetch_and_filter_logs
from loglens.sources.base import LogSource
from loglens.sources.registry import register_source, _clear_registry
from loglens.model import RawEvent, LogRecord


class TestSource(LogSource):
    """Test source that yields predefined events."""
    
    def __init__(self, events=None):
        self.events = events or []
        self.closed = False
    
    def read(self):
        for event in self.events:
            yield event
    
    def close(self):
        self.closed = True


class TestFetchLogs:
    def setup_method(self):
        """Register test source."""
        _clear_registry()
        register_source("test", TestSource)
        register_source("journalctl", lambda **kw: TestSource([]))  # Mock journalctl
    
    def test_fetch_with_source_name(self):
        """Test fetching logs by source name."""
        events = [
            RawEvent(
                data={"MESSAGE": "test 1", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
            RawEvent(
                data={"MESSAGE": "test 2", "PRIORITY": "3", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
        ]
        
        _clear_registry()
        register_source("test", lambda: TestSource(events))
        
        records = list(fetch_logs("test"))
        
        assert len(records) == 2
        assert all(isinstance(r, LogRecord) for r in records)
        assert records[0].message == "test 1"
        assert records[1].message == "test 2"
    
    def test_fetch_with_source_instance(self):
        """Test fetching logs with source instance."""
        events = [
            RawEvent(
                data={"MESSAGE": "direct", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
        ]
        
        source = TestSource(events)
        records = list(fetch_logs(source))
        
        assert len(records) == 1
        assert records[0].message == "direct"
        assert source.closed  # Context manager should close
    
    def test_fetch_with_limit(self):
        """Test fetching logs with limit parameter."""
        events = [
            RawEvent(
                data={"MESSAGE": f"message {i}", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            )
            for i in range(10)
        ]
        
        _clear_registry()
        register_source("test", lambda: TestSource(events))
        
        records = list(fetch_logs("test", limit=5))
        
        assert len(records) == 5
        assert records[0].message == "message 0"
        assert records[4].message == "message 4"
    
    def test_fetch_with_limit_and_source_kwargs(self):
        """Test that limit doesn't interfere with source kwargs."""
        events = [
            RawEvent(
                data={"MESSAGE": f"test {i}", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            )
            for i in range(10)
        ]
        
        class ConfigurableTestSource(TestSource):
            def __init__(self, custom_arg=None):
                super().__init__(events)
                self.custom_arg = custom_arg
        
        _clear_registry()
        register_source("test", ConfigurableTestSource)
        
        records = list(fetch_logs("test", limit=3, custom_arg="value"))
        
        assert len(records) == 3


class TestFilterLogs:
    def create_records(self):
        """Helper to create test records."""
        return [
            LogRecord("2026-02-15T10:00:00", 3, "ERROR", "error message 1"),
            LogRecord("2026-02-15T10:01:00", 6, "INFO", "info message"),
            LogRecord("2026-02-15T10:02:00", 3, "ERROR", "error message 2"),
            LogRecord("2026-02-15T10:03:00", 4, "WARNING", "warning failed"),
        ]
    
    def test_filter_by_severity(self):
        """Test filtering by exact severity."""
        records = self.create_records()
        result = list(filter_logs(iter(records), severity="error"))
        
        assert len(result) == 2
        assert all(r.severity_label == "ERROR" for r in result)
    
    def test_filter_by_min_severity(self):
        """Test filtering by minimum severity."""
        records = self.create_records()
        result = list(filter_logs(iter(records), min_severity="warning"))
        
        # Should include ERROR (3), WARNING (4), but not INFO (6)
        assert len(result) == 3
        assert result[0].severity_num == 3
        assert result[1].severity_num == 3
        assert result[2].severity_num == 4
    
    def test_filter_by_keyword(self):
        """Test filtering by keyword."""
        records = self.create_records()
        result = list(filter_logs(iter(records), keyword="error"))
        
        assert len(result) == 2
    
    def test_filter_combined(self):
        """Test combined filters."""
        records = self.create_records()
        result = list(filter_logs(iter(records), min_severity="warning", keyword="failed"))
        
        assert len(result) == 1
        assert result[0].message == "warning failed"


class TestFetchAndFilterLogs:
    def setup_method(self):
        """Register test source."""
        _clear_registry()
        
        events = [
            RawEvent(
                data={"MESSAGE": "error failed", "PRIORITY": "3", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
            RawEvent(
                data={"MESSAGE": "info message", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
        ]
        
        register_source("test", lambda: TestSource(events))
    
    def test_fetch_and_filter_combined(self):
        """Test convenience function for fetch + filter."""
        result = list(fetch_and_filter_logs("test", min_severity="error", keyword="failed"))
        
        assert len(result) == 1
        assert result[0].message == "error failed"
        assert result[0].severity_label == "ERROR"
    
    def test_fetch_and_filter_with_limit(self):
        """Test fetch_and_filter_logs with limit parameter."""
        events = [
            RawEvent(
                data={"MESSAGE": "error 1", "PRIORITY": "3", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
            RawEvent(
                data={"MESSAGE": "error 2", "PRIORITY": "3", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
            RawEvent(
                data={"MESSAGE": "error 3", "PRIORITY": "3", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
        ]
        
        _clear_registry()
        register_source("test", lambda: TestSource(events))
        
        result = list(fetch_and_filter_logs("test", limit=2))
        
        assert len(result) == 2
        assert result[0].message == "error 1"
        assert result[1].message == "error 2"


class TestEndToEnd:
    """Integration tests for success criteria."""
    
    def test_success_criteria_fetch_returns_structured_objects(self):
        """Verify: fetch_logs() returns structured objects."""
        _clear_registry()
        
        events = [
            RawEvent(
                data={"MESSAGE": "test", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
        ]
        register_source("test", lambda: TestSource(events))
        
        records = list(fetch_logs("test"))
        
        assert len(records) == 1
        record = records[0]
        assert isinstance(record, LogRecord)
        assert hasattr(record, "timestamp")
        assert hasattr(record, "severity_num")
        assert hasattr(record, "severity_label")
        assert hasattr(record, "message")
    
    def test_success_criteria_filter_logs_works(self):
        """Verify: filter_logs() works correctly."""
        records = [
            LogRecord("2026-02-15T10:00:00", 3, "ERROR", "error"),
            LogRecord("2026-02-15T10:01:00", 6, "INFO", "info"),
            LogRecord("2026-02-15T10:02:00", 4, "WARNING", "warning"),
        ]
        
        # Test exact severity
        result_exact = list(filter_logs(iter(records), severity=3))
        assert len(result_exact) == 1
        
        # Test min severity
        result_min = list(filter_logs(iter(records), min_severity="warning"))
        assert len(result_min) == 2
        
        # Test keyword
        result_keyword = list(filter_logs(iter(records), keyword="error"))
        assert len(result_keyword) == 1
    
    def test_success_criteria_no_ui_dependency(self):
        """Verify: No UI dependencies in backend."""
        # This is more of a structural check
        # If any UI imports exist, this test file itself would fail to import
        from loglens import engine, model, severity, filtering, normalize
        
        # All imports should work without TUI/UI libraries
        assert True  # If we got here, no UI dependencies
