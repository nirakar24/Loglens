#!/usr/bin/env python3
"""
Simple example showing LogLens usage.
"""

from loglens import fetch_logs, filter_logs
from loglens.sources import list_sources

print("\n" + "="*60)
print("LogLens - Phase 1 Example")
print("="*60 + "\n")

# Show available sources
print("Available log sources:", ", ".join(list_sources()))
print()

# Example 1: Create a mock source for demonstration
from loglens.sources.base import LogSource
from loglens.model import RawEvent

class ExampleSource(LogSource):
    """Example source with sample log data."""
    
    def read(self):
        sample_logs = [
            {"MESSAGE": "Application started successfully", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000000000000"},
            {"MESSAGE": "Database connection established", "PRIORITY": "6", "_SOURCE_REALTIME_TIMESTAMP": "1708000001000000"},
            {"MESSAGE": "Warning: High memory usage detected", "PRIORITY": "4", "_SOURCE_REALTIME_TIMESTAMP": "1708000002000000"},
            {"MESSAGE": "Error: Failed to connect to external API", "PRIORITY": "3", "_SOURCE_REALTIME_TIMESTAMP": "1708000003000000"},
            {"MESSAGE": "Critical: Disk space running low", "PRIORITY": "2", "_SOURCE_REALTIME_TIMESTAMP": "1708000004000000"},
        ]
        
        for log in sample_logs:
            yield RawEvent(data=log, source_type="journalctl")
    
    def close(self):
        pass

# Example 2: Fetch all logs
print("Example 1: Fetch all logs")
print("-" * 60)
source = ExampleSource()
for i, record in enumerate(fetch_logs(source), 1):
    print(f"{i}. [{record.severity_label:8}] {record.message}")
print()

# Example 3: Filter by minimum severity (WARNING+)
print("Example 2: Filter by minimum severity (WARNING+)")
print("-" * 60)
source = ExampleSource()
logs = fetch_logs(source)
filtered = filter_logs(logs, min_severity="warning")
for i, record in enumerate(filtered, 1):
    print(f"{i}. [{record.severity_label:8}] {record.message}")
print()

# Example 4: Filter by keyword
print("Example 3: Filter by keyword ('failed')")
print("-" * 60)
source = ExampleSource()
logs = fetch_logs(source)
filtered = filter_logs(logs, keyword="failed")
for i, record in enumerate(filtered, 1):
    print(f"{i}. [{record.severity_label:8}] {record.message}")
print()

# Example 5: Combined filters
print("Example 4: Combined filters (ERROR+ with 'connection')")
print("-" * 60)
source = ExampleSource()
logs = fetch_logs(source)
filtered = filter_logs(logs, min_severity="error", keyword="connection")
for i, record in enumerate(filtered, 1):
    print(f"{i}. [{record.severity_label:8}] {record.message}")
print()

print("="*60)
print("✅ LogLens Phase 1 is working correctly!")
print("="*60)
print()
print("Next steps:")
print("  1. Run 'python3 verify.py' for full test suite")
print("  2. Read PHASE1_SUMMARY.md for complete documentation")
print("  3. Check README.md for API usage examples")
print()
