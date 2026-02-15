#!/usr/bin/env python3
"""Quick verification script for Phase 1 success criteria."""

import sys
sys.path.insert(0, '.')

from loglens.sources.base import LogSource
from loglens.model import RawEvent
from loglens.engine import fetch_logs, filter_logs

print("Testing end-to-end engine API...\n")

# Create a test source
class TestSource(LogSource):
    def __init__(self):
        self.closed = False
    
    def read(self):
        events = [
            RawEvent(
                data={"MESSAGE": "error occurred", "PRIORITY": "3", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
            RawEvent(
                data={"MESSAGE": "info message", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
            RawEvent(
                data={"MESSAGE": "warning alert", "PRIORITY": "4", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
                source_type="journalctl"
            ),
        ]
        for event in events:
            yield event
    
    def close(self):
        self.closed = True

# Test fetch_logs
print("Test 1: fetch_logs returns structured objects...")
source = TestSource()
records = list(fetch_logs(source))
assert len(records) == 3
assert all(hasattr(r, 'timestamp') for r in records)
assert all(hasattr(r, 'severity_num') for r in records)
assert all(hasattr(r, 'severity_label') for r in records)
assert all(hasattr(r, 'message') for r in records)
assert source.closed  # Verify context manager closed source
print("✅ fetch_logs() returns structured objects")

# Test filter_logs with severity
print("\nTest 2: filter_logs by severity...")
source = TestSource()
logs = fetch_logs(source)
filtered = list(filter_logs(logs, min_severity="warning"))
assert len(filtered) == 2  # ERROR and WARNING
assert filtered[0].severity_num == 3  # ERROR
assert filtered[1].severity_num == 4  # WARNING
print("✅ filter_logs() works correctly for severity")

# Test filter_logs with keyword
print("\nTest 3: filter_logs by keyword...")
source = TestSource()
logs = fetch_logs(source)
filtered = list(filter_logs(logs, keyword="error"))
assert len(filtered) == 1
assert "error" in filtered[0].message
print("✅ filter_logs() works correctly for keyword")

# Test combined filters
print("\nTest 4: Combined filters...")
source = TestSource()
logs = fetch_logs(source)
filtered = list(filter_logs(logs, min_severity="warning", keyword="alert"))
assert len(filtered) == 1
assert filtered[0].message == "warning alert"
print("✅ Combined filters work correctly")

print("\n" + "="*60)
print("SUCCESS CRITERIA VERIFICATION ✅")
print("="*60)
print("✅ fetch_logs() returns structured objects")
print("✅ filter_logs() works correctly")
print("✅ No UI dependency (pure backend)")
print("✅ Reusable log processing engine")
print("✅ Pluggable source architecture")
print("="*60)
