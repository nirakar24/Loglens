# Phase 1 Issue Resolution Report

## Summary

All identified issues from manual testing have been addressed with diagnostic capabilities and improved error handling.

## Issues Resolved

### ✅ Issue #1: Constructor vs Runtime Argument Mixing
**Status**: RESOLVED  
**Changes**: 
- Added explicit `limit` parameter to `fetch_logs()` 
- Separated fetch-time parameters from source constructor parameters
- Updated `fetch_and_filter_logs()` to support limit

**Test**:
```python
from loglens import fetch_logs
count = sum(1 for _ in fetch_logs(limit=5000))
print(f"Fetched: {count}")  # Works without TypeError
```

### ✅ Issue #2: read() Method Signature (Non-issue)
**Status**: CLARIFIED  
**Explanation**: The architecture is correct - runtime parameters belong in the constructor, not `read()`. The `read()` method should be a simple iterator with no parameters. This is working as designed.

### 🔍 Issue #3: CRIT Severity Mismatch  
**Status**: DIAGNOSTIC TOOLS ADDED  
**Changes**:
- Added `warn_on_errors=True` parameter to surface data quality issues
- Added statistics tracking in normalization layer
- Improved priority field handling with detailed error tracking
- Created `diagnose.py` script to investigate count mismatches

**How to investigate**:
```python
from loglens import fetch_logs, get_diagnostics

# Fetch with warnings enabled
logs = list(fetch_logs(warn_on_errors=True))

# Check diagnostics
diag = get_diagnostics()
print(f"Missing PRIORITY: {diag['normalization']['missing_priority']}")
print(f"Invalid PRIORITY: {diag['normalization']['invalid_priority']}")

# Or run comprehensive diagnostic
# python3 diagnose.py
```

### 🔍 Issue #4: Warning+ Count Mismatch (169 vs 185)
**Status**: DIAGNOSTIC TOOLS ADDED  
**Changes**:
- Added JSON parsing error tracking in `JournalctlSource`
- Statistics now show: total_lines, empty_lines, json_errors, events_yielded
- Can access source statistics via `source.stats` after reading
- Warning messages printed to stderr when entries are skipped

**Example**:
```python
from loglens.sources.journalctl import JournalctlSource

source = JournalctlSource(warn_on_errors=True)
logs = list(source.read())
source.close()

print(f"Total lines read: {source.stats['total_lines']}")
print(f"JSON errors: {source.stats['json_errors']}")
print(f"Events yielded: {source.stats['events_yielded']}")

# Difference reveals where entries were lost
lost = source.stats['total_lines'] - source.stats['events_yielded']
print(f"Entries lost: {lost}")
```

### ✅ Issue #5: Silent Normalization Drops
**Status**: RESOLVED  
**Changes**:
- No longer silent - warnings printed to stderr when `warn_on_errors=True`
- Global normalization statistics track all missing/invalid fields
- Added `get_diagnostics()` function to retrieve statistics
- Added `reset_diagnostics()` to clear counters between runs

**Statistics tracked**:
- `total`: Total events normalized
- `missing_priority`: Events without PRIORITY field (default to INFO) 
- `invalid_priority`: Events with out-of-range PRIORITY values
- `missing_timestamp`: Events without valid timestamp
- `missing_message`: Events without MESSAGE field

## New APIs

### get_diagnostics()
Returns diagnostic information about log processing:
```python
from loglens import fetch_logs, get_diagnostics

list(fetch_logs(limit=100, warn_on_errors=True))
diag = get_diagnostics()

print("Normalization stats:")
for key, value in diag['normalization'].items():
    print(f"  {key}: {value}")
```

### reset_diagnostics()
Resets all diagnostic counters:
```python
from loglens import reset_diagnostics

reset_diagnostics()  # Clear counters before next run
```

### warn_on_errors parameter
Enable warnings for data quality issues:
```python
# Prints warnings to stderr for skipped/problematic entries
logs = fetch_logs(warn_on_errors=True)

# Or with filtering
logs = fetch_and_filter_logs(
    min_severity="warning",
    warn_on_errors=True,
    units=["nginx.service"]
)
```

### source.stats attribute
JournalctlSource now tracks reading statistics:
```python
from loglens.sources.journalctl import JournalctlSource

source = JournalctlSource(warn_on_errors=True)
events = list(source.read())
source.close()

# Available statistics
print(source.stats['total_lines'])      # Lines read from journalctl
print(source.stats['empty_lines'])      # Empty lines skipped
print(source.stats['json_errors'])      # JSON parse errors
print(source.stats['events_yielded'])   # Successfully parsed events
```

## Diagnostic Script

Run `python3 diagnose.py` for comprehensive diagnostic report including:
- Source-level statistics (lines read, parse errors)
- Normalization statistics (missing fields, invalid values)
- Severity distribution
- Comparison with raw journalctl counts
- Data loss analysis
- Specific recommendations

## Files Modified

1. **loglens/sources/journalctl.py**
   - Added statistics tracking
   - Added `warn_on_errors` parameter
   - JSON parse errors now tracked and optionally warned

2. **loglens/normalize.py**
   - Added global normalization statistics
   - Added `warn_on_missing` parameter
   - Better priority field validation
   - Exported `get_normalization_stats()` and `reset_normalization_stats()`

3. **loglens/engine.py**
   - Added `warn_on_errors` parameter to `fetch_logs()` and `fetch_and_filter_logs()`
   - Added `get_diagnostics()` function
   - Added `reset_diagnostics()` function
   - Pass warnings through to sources and normalizers

4. **loglens/__init__.py**
   - Exported `get_diagnostics` and `reset_diagnostics`

5. **New files**:
   - `diagnose.py` - Comprehensive diagnostic script

## Testing

Basic verification:
```bash
# Test diagnostics
python3 -c "
from loglens import fetch_logs, get_diagnostics
list(fetch_logs(limit=10))
print(get_diagnostics())
"

# Test with warnings
python3 -c "
from loglens import fetch_logs
list(fetch_logs(limit=10, warn_on_errors=True))
" 2>&1 | grep -i warning
```

Comprehensive diagnostics:
```bash
python3 diagnose.py
```

## Next Steps

If count mismatches persist after running diagnostics:

1. **Run diagnose.py** to get detailed report2. **Check JSON parse errors** - if > 0, investigate journalctl output format
3. **Check normalization stats** - look for missing/invalid PRIORITY fields
4. **Compare severity distributions** - look for misclassified entries
5. **Inspect raw data** - check journalctl JSON output directly:
   ```bash
   journalctl --since "24 hours ago" -o json | head -n 20
   ```

## Architecture Improvements

The diagnostic layer adds **visibility without breaking abstractions**:
- Sources track their own read statistics
- Normalizers track field quality issues
- Engine provides unified diagnostic API
- Optional warnings for real-time feedback
- Statistics accessible programmatically for automated testing

This enables debugging count mismatches and data quality issues without modifying core business logic.
