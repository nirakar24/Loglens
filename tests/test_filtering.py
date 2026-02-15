"""Tests for filtering logic."""

import pytest
from loglens.model import LogRecord
from loglens.filtering import filter_logs


def create_record(severity_num, message, severity_label=None):
    """Helper to create test LogRecord."""
    from loglens.severity import priority_to_label
    if severity_label is None:
        severity_label = priority_to_label(severity_num)
    return LogRecord(
        timestamp="2026-02-15T10:00:00",
        severity_num=severity_num,
        severity_label=severity_label,
        message=message,
    )


class TestFilterBySeverityExact:
    def test_exact_match_numeric(self):
        """Test filtering by exact numeric severity."""
        records = [
            create_record(3, "error msg"),
            create_record(6, "info msg"),
            create_record(3, "another error"),
        ]
        
        result = list(filter_logs(iter(records), severity=3))
        assert len(result) == 2
        assert all(r.severity_num == 3 for r in result)
    
    def test_exact_match_label(self):
        """Test filtering by exact severity label."""
        records = [
            create_record(3, "error msg"),
            create_record(6, "info msg"),
            create_record(4, "warning msg"),
        ]
        
        result = list(filter_logs(iter(records), severity="warning"))
        assert len(result) == 1
        assert result[0].severity_num == 4


class TestFilterByMinSeverity:
    def test_minimum_severity_threshold(self):
        """Test filtering by minimum severity (threshold)."""
        records = [
            create_record(0, "emerg"),  # Should pass
            create_record(3, "error"),  # Should pass
            create_record(4, "warning"),  # Should pass (exact match)
            create_record(6, "info"),  # Should fail (less severe)
            create_record(7, "debug"),  # Should fail
        ]
        
        result = list(filter_logs(iter(records), min_severity="warning"))
        assert len(result) == 3
        assert all(r.severity_num <= 4 for r in result)
    
    def test_min_severity_label(self):
        """Test minimum severity with label input."""
        records = [
            create_record(2, "crit"),
            create_record(3, "error"),
            create_record(6, "info"),
        ]
        
        result = list(filter_logs(iter(records), min_severity="error"))
        assert len(result) == 2
        assert result[0].severity_num == 2
        assert result[1].severity_num == 3


class TestFilterByKeyword:
    def test_keyword_case_insensitive(self):
        """Test keyword filtering (case-insensitive by default)."""
        records = [
            create_record(6, "Failed to connect"),
            create_record(6, "Connection successful"),
            create_record(6, "FAILED attempt"),
        ]
        
        result = list(filter_logs(iter(records), keyword="failed"))
        assert len(result) == 2
        assert "failed" in result[0].message.lower()
        assert "failed" in result[1].message.lower()
    
    def test_keyword_case_sensitive(self):
        """Test keyword filtering (case-sensitive)."""
        records = [
            create_record(6, "Failed to connect"),
            create_record(6, "failed attempt"),
            create_record(6, "success"),
        ]
        
        result = list(filter_logs(iter(records), keyword="Failed", case_sensitive=True))
        assert len(result) == 1
        assert "Failed" in result[0].message


class TestCombinedFilters:
    def test_severity_and_keyword(self):
        """Test combining severity and keyword filters."""
        records = [
            create_record(3, "error: failed to start"),
            create_record(3, "error: success"),
            create_record(6, "info: failed to connect"),
        ]
        
        result = list(filter_logs(iter(records), severity=3, keyword="failed"))
        assert len(result) == 1
        assert result[0].severity_num == 3
        assert "failed" in result[0].message.lower()
    
    def test_min_severity_and_keyword(self):
        """Test combining minimum severity and keyword filters."""
        records = [
            create_record(2, "crit: connection failed"),
            create_record(3, "error: failed to start"),
            create_record(4, "warning: failed"),
            create_record(6, "info: failed"),
        ]
        
        result = list(filter_logs(iter(records), min_severity="warning", keyword="failed"))
        assert len(result) == 3  # crit, error, warning all pass (info fails severity)
        assert all(r.severity_num <= 4 for r in result)
    
    def test_mutually_exclusive_severity_filters(self):
        """Test that severity and min_severity cannot be used together."""
        records = [create_record(6, "test")]
        
        with pytest.raises(ValueError, match="Cannot specify both"):
            list(filter_logs(iter(records), severity=3, min_severity=4))


class TestEmptyResults:
    def test_no_matches(self):
        """Test filtering with no matches returns empty iterator."""
        records = [
            create_record(6, "info msg"),
            create_record(7, "debug msg"),
        ]
        
        result = list(filter_logs(iter(records), severity=3))
        assert len(result) == 0
    
    def test_empty_input(self):
        """Test filtering empty input returns empty iterator."""
        result = list(filter_logs(iter([]), severity=3))
        assert len(result) == 0
