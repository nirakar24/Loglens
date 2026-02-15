"""Tests for normalization logic."""

import pytest
from loglens.model import RawEvent, LogRecord
from loglens.normalize import normalize_event, NormalizationError


class TestNormalizeJournalctl:
    def test_basic_journalctl_event(self):
        """Test normalization of a typical journald event."""
        raw = RawEvent(
            data={
                "MESSAGE": "Service started successfully",
                "PRIORITY": "6",
                "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000",  # Microseconds
                "_SYSTEMD_UNIT": "example.service",
            },
            source_type="journalctl",
        )
        
        record = normalize_event(raw)
        
        assert isinstance(record, LogRecord)
        assert record.message == "Service started successfully"
        assert record.severity_num == 6
        assert record.severity_label == "INFO"
        assert record.timestamp.startswith("2024-02")  # Rough check
        assert record.raw == raw.data
    
    def test_journalctl_with_numeric_priority(self):
        """Test different priority levels."""
        for priority in range(8):
            raw = RawEvent(
                data={
                    "MESSAGE": f"Test message {priority}",
                    "PRIORITY": str(priority),
                    "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000",
                },
                source_type="journalctl",
            )
            
            record = normalize_event(raw)
            assert record.severity_num == priority
    
    def test_journalctl_missing_priority(self):
        """Test that missing priority defaults to INFO (6)."""
        raw = RawEvent(
            data={
                "MESSAGE": "Message without priority",
                "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000",
            },
            source_type="journalctl",
        )
        
        record = normalize_event(raw)
        assert record.severity_num == 6
        assert record.severity_label == "INFO"
    
    def test_journalctl_alternative_timestamp(self):
        """Test fallback to __REALTIME_TIMESTAMP."""
        raw = RawEvent(
            data={
                "MESSAGE": "Test",
                "PRIORITY": "6",
                "__REALTIME_TIMESTAMP": "1708000000000000",
            },
            source_type="journalctl",
        )
        
        record = normalize_event(raw)
        assert record.timestamp  # Should have valid timestamp
    
    def test_journalctl_missing_timestamp(self):
        """Test that missing timestamp uses current time."""
        raw = RawEvent(
            data={
                "MESSAGE": "Test",
                "PRIORITY": "6",
            },
            source_type="journalctl",
        )
        
        record = normalize_event(raw)
        assert record.timestamp  # Should still have valid timestamp
    
    def test_journalctl_invalid_data_type(self):
        """Test that non-dict data raises error."""
        raw = RawEvent(
            data="not a dict",
            source_type="journalctl",
        )
        
        with pytest.raises(NormalizationError, match="must be a dict"):
            normalize_event(raw)


class TestNormalizeFileJsonl:
    def test_basic_jsonl_event(self):
        """Test normalization of JSON Lines event."""
        raw = RawEvent(
            data={
                "timestamp": "2026-02-15T10:00:00",
                "level": "error",
                "message": "Connection failed",
            },
            source_type="file_jsonl",
        )
        
        record = normalize_event(raw)
        
        assert record.message == "Connection failed"
        assert record.severity_num == 3  # error
        assert record.severity_label == "ERROR"
        assert "2026-02-15" in record.timestamp
    
    def test_jsonl_various_level_names(self):
        """Test different level field variations."""
        levels = [
            ("debug", 7),
            ("info", 6),
            ("warn", 4),
            ("warning", 4),
            ("error", 3),
            ("critical", 2),
        ]
        
        for level_str, expected_num in levels:
            raw = RawEvent(
                data={"level": level_str, "message": "test"},
                source_type="file_jsonl",
            )
            record = normalize_event(raw)
            assert record.severity_num == expected_num
    
    def test_jsonl_missing_fields(self):
        """Test JSONL with missing optional fields defaults gracefully."""
        raw = RawEvent(
            data={"msg": "Minimal event"},
            source_type="file_jsonl",
        )
        
        record = normalize_event(raw)
        assert record.message == "Minimal event"
        assert record.severity_num == 6  # Default INFO


class TestNormalizeFileText:
    def test_basic_text_line(self):
        """Test normalization of plain text line."""
        raw = RawEvent(
            data="2026-02-15 10:00:00 ERROR Connection failed",
            source_type="file_text",
        )
        
        record = normalize_event(raw)
        
        assert record.message == "2026-02-15 10:00:00 ERROR Connection failed"
        assert record.severity_num == 6  # Default INFO
        assert record.severity_label == "INFO"
    
    def test_text_invalid_data_type(self):
        """Test that non-string data raises error."""
        raw = RawEvent(
            data={"not": "a string"},
            source_type="file_text",
        )
        
        with pytest.raises(NormalizationError, match="must be a string"):
            normalize_event(raw)


class TestUnknownSourceType:
    def test_unknown_source_raises_error(self):
        """Test that unknown source types raise error."""
        raw = RawEvent(
            data={"test": "data"},
            source_type="unknown_source",
        )
        
        with pytest.raises(NormalizationError, match="Unknown source type"):
            normalize_event(raw)
