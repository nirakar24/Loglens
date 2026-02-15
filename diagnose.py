#!/usr/bin/env python3
"""
Diagnostic script to investigate count mismatches and data quality issues.

This script helps debug Issues #3, #4, and #5 by providing detailed statistics
about what's happening during log fetching and normalization.
"""

import sys
sys.path.insert(0, '.')

from loglens import fetch_logs, filter_logs, get_diagnostics, reset_diagnostics

print("="*70)
print("LogLens Diagnostic Report")
print("="*70)
print()

# Test 1: Fetch all logs with diagnostics
print("Test 1: Fetching logs from journalctl (last 24h) with diagnostics")
print("-"*70)

reset_diagnostics()
from loglens.sources.journalctl import JournalctlSource

# Create source and inspect statistics
source = JournalctlSource(warn_on_errors=True)
print(f"Fetching logs...")
records = list(source.read())
print(f"\nSource-level statistics:")
print(f"  Total lines read:     {source.stats['total_lines']}")
print(f"  Empty lines skipped:  {source.stats['empty_lines']}")
print(f"  JSON parse errors:    {source.stats['json_errors']}")
print(f"  Events yielded:       {source.stats['events_yielded']}")
source.close()

# Now normalize them
print(f"\nNormalizing {len(records)} raw events...")
from loglens.normalize import normalize_event, get_normalization_stats

normalized = []
for event in records:
    try:
        normalized.append(normalize_event(event, warn_on_missing=True))
    except Exception as e:
        print(f"  Normalization error: {e}", file=sys.stderr)

print(f"\nNormalization statistics:")
norm_stats = get_normalization_stats()
print(f"  Total normalized:       {norm_stats['total']}")
print(f"  Missing PRIORITY:       {norm_stats['missing_priority']}")
print(f"  Invalid PRIORITY:       {norm_stats['invalid_priority']}")
print(f"  Missing timestamp:      {norm_stats['missing_timestamp']}")
print(f"  Missing MESSAGE:        {norm_stats['missing_message']}")

print(f"\n  Records after normalization: {len(normalized)}")
print()

# Test 2: Severity distribution
print("Test 2: Severity distribution")
print("-"*70)
from collections import Counter

severity_counts = Counter(r.severity_label for r in normalized)
for severity in ["EMERG", "ALERT", "CRIT", "ERROR", "WARNING", "NOTICE", "INFO", "DEBUG"]:
    count = severity_counts.get(severity, 0)
    print(f"  {severity:8s}: {count:5d}")

print()

# Test 3: Compare with raw journalctl output
print("Test 3: Comparing with raw journalctl counts")
print("-"*70)
import subprocess

def get_journalctl_count(priority_filter=None):
    """Get count from journalctl directly."""
    cmd = ["journalctl", "--since", "24 hours ago", "--no-pager"]
    if priority_filter is not None:
        cmd.extend(["--priority", str(priority_filter)])
    
    try:
        result = subprocess.run(
            cmd + ["--output=cat"],
            capture_output=True,
            text=True
        )
        # Count non-empty lines
        lines = [l for l in result.stdout.split('\n') if l.strip()]
        return len(lines)
    except Exception as e:
        return f"Error: {e}"

print("Raw journalctl counts (non-JSON):")
print(f"  All logs:           {get_journalctl_count()}")
print(f"  CRIT and above (≤2): {get_journalctl_count(2)}")
print(f"  ERROR and above (≤3): {get_journalctl_count(3)}")
print(f"  WARNING and above (≤4): {get_journalctl_count(4)}")

print()
print("LogLens counts:")
print(f"  All logs:           {len(normalized)}")
crit_count = sum(1 for r in normalized if r.severity_num <= 2)
error_count = sum(1 for r in normalized if r.severity_num <= 3)
warning_count = sum(1 for r in normalized if r.severity_num <= 4)
print(f"  CRIT and above (≤2): {crit_count}")
print(f"  ERROR and above (≤3): {error_count}")
print(f"  WARNING and above (≤4): {warning_count}")

print()

# Test 4: Show sample CRIT entries if any
print("Test 4: Sample CRIT entries (if any)")
print("-"*70)
crit_entries = [r for r in normalized if r.severity_num <= 2]
if crit_entries:
    for i, entry in enumerate(crit_entries[:3], 1):
        print(f"{i}. [{entry.severity_label}] {entry.message[:60]}")
else:
    print("  No CRIT entries found in LogLens")
    
    # Check raw journalctl
    print("\n  Checking raw journalctl for CRIT entries:")
    try:
        result = subprocess.run(
            ["journalctl", "--since", "24 hours ago", "--priority", "2", "-n", "3", "--no-pager"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(result.stdout[:500])
        else:
            print("  No CRIT entries found in journalctl either")
    except Exception as e:
        print(f"  Error checking journalctl: {e}")

print()
print("="*70)
print("Diagnostic Summary")
print("="*70)

# Calculate data loss
json_errors = source.stats['json_errors']
norm_dropped = source.stats['events_yielded'] - len(normalized)

print(f"\nData Loss Analysis:")
print(f"  JSON parse errors:        {json_errors}")
print(f"  Events yielded by source: {source.stats['events_yielded']}")
print(f"  Successfully normalized:  {len(normalized)}")
print(f"  Lost in normalization:    {norm_dropped}")
print(f"  Total data loss:          {json_errors + norm_dropped}")

if json_errors > 0:
    print(f"\n⚠️  {json_errors} log entries were skipped due to JSON parsing errors")

if norm_dropped > 0:
    print(f"\n⚠️  {norm_dropped} events were lost during normalization")

if norm_stats['missing_priority'] > 0:
    print(f"\n⚠️  {norm_stats['missing_priority']} entries had missing PRIORITY (defaulted to INFO)")

if norm_stats['invalid_priority'] > 0:
    print(f"\n⚠️  {norm_stats['invalid_priority']} entries had invalid PRIORITY values")

print()
print("Recommendations:")
if json_errors > 0:
    print("  • Re-run with warn_on_errors=True to see which lines are malformed")
    print("  • Check journalctl JSON output: journalctl --output=json | head")
if crit_count == 0 and get_journalctl_count(2) > 0:
    print("  • CRIT entry mismatch detected - investigate priority field handling")
if warning_count < get_journalctl_count(4):
    diff = get_journalctl_count(4) - warning_count
    print(f"  • {diff} WARNING+ entries missing - check for silent drops or field issues")

print()
