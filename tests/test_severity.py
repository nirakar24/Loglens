"""Tests for severity mapping utilities."""

import pytest
from loglens.severity import (
    priority_to_label,
    label_to_priority,
    is_at_least_severity,
    PRIORITY_LABELS,
)


class TestPriorityToLabel:
    def test_all_valid_priorities(self):
        """Test conversion of all valid numeric priorities."""
        for num, label in PRIORITY_LABELS.items():
            assert priority_to_label(num) == label
    
    def test_invalid_priority_raises_error(self):
        """Test that invalid priorities raise ValueError."""
        with pytest.raises(ValueError, match="Invalid priority"):
            priority_to_label(-1)
        
        with pytest.raises(ValueError, match="Invalid priority"):
            priority_to_label(8)


class TestLabelToPriority:
    def test_standard_labels(self):
        """Test conversion of standard severity labels."""
        assert label_to_priority("EMERG") == 0
        assert label_to_priority("ALERT") == 1
        assert label_to_priority("CRIT") == 2
        assert label_to_priority("ERROR") == 3
        assert label_to_priority("WARNING") == 4
        assert label_to_priority("NOTICE") == 5
        assert label_to_priority("INFO") == 6
        assert label_to_priority("DEBUG") == 7
    
    def test_case_insensitive(self):
        """Test that labels are case-insensitive."""
        assert label_to_priority("error") == 3
        assert label_to_priority("Error") == 3
        assert label_to_priority("ERROR") == 3
    
    def test_aliases(self):
        """Test common aliases."""
        assert label_to_priority("err") == 3
        assert label_to_priority("warn") == 4
        assert label_to_priority("critical") == 2
        assert label_to_priority("emergency") == 0
    
    def test_numeric_input(self):
        """Test that numeric inputs work."""
        assert label_to_priority(3) == 3
        assert label_to_priority(6) == 6
        assert label_to_priority("5") == 5
    
    def test_invalid_label_raises_error(self):
        """Test that unknown labels raise ValueError."""
        with pytest.raises(ValueError, match="Unknown severity label"):
            label_to_priority("invalid")
    
    def test_invalid_number_raises_error(self):
        """Test that out-of-range numbers raise ValueError."""
        with pytest.raises(ValueError, match="Invalid priority number"):
            label_to_priority(10)
        
        with pytest.raises(ValueError, match="Invalid priority number"):
            label_to_priority(-1)


class TestIsAtLeastSeverity:
    def test_exact_match(self):
        """Test exact severity match."""
        assert is_at_least_severity(3, "error") is True
        assert is_at_least_severity(6, 6) is True
    
    def test_more_severe(self):
        """Test more severe (lower number) passes threshold."""
        assert is_at_least_severity(0, "warning") is True  # EMERG >= WARNING
        assert is_at_least_severity(2, 4) is True  # CRIT >= WARNING
    
    def test_less_severe(self):
        """Test less severe (higher number) fails threshold."""
        assert is_at_least_severity(6, "error") is False  # INFO < ERROR
        assert is_at_least_severity(7, 3) is False  # DEBUG < ERROR
    
    def test_string_and_numeric_input(self):
        """Test mixed string and numeric thresholds."""
        assert is_at_least_severity(3, "error") is True
        assert is_at_least_severity(3, 3) is True
        assert is_at_least_severity(4, "warning") is True
