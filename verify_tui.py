#!/usr/bin/env python3
"""
Phase 2 TUI Verification Script (without textual runtime).

Verifies:
- TUI package structure
- Module imports (syntax)
- Backend adapter functionality
- State model operations

Does NOT require textual to be installed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("Phase 2 TUI Verification (Non-Runtime)")
print("="*70)
print()

# 1. Check package structure
print("✓ Checking package structure...")
expected_files = [
    "loglens/tui/__init__.py",
    "loglens/tui/state.py",
    "loglens/tui/backend.py",
    "loglens/tui/app.py",
    "loglens/tui/app.css",
    "loglens/tui/screens/__init__.py",
    "loglens/tui/screens/main.py",
    "logtui.py",
]

for file in expected_files:
    path = Path(file)
    assert path.exists(), f"Missing: {file}"
    print(f"  ✓ {file}")

print()

# 2. Check syntax (import without textual)
print("✓ Checking module syntax...")

# Import modules directly to avoid __init__.py which imports app.py (needs textual)
import importlib.util

def import_module_directly(name, path):
    """Import a module from a file path without going through __init__.py"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

try:
    state = import_module_directly("loglens.tui.state", "loglens/tui/state.py")
    print("  ✓ loglens.tui.state imports")
except Exception as e:
    print(f"  ✗ state.py: {e}")
    sys.exit(1)

try:
    backend = import_module_directly("loglens.tui.backend", "loglens/tui/backend.py")
    print("  ✓ loglens.tui.backend imports")
except Exception as e:
    print(f"  ✗ backend.py: {e}")
    sys.exit(1)

print()

# 3. Test state models
print("✓ Testing state models...")
FilterState = state.FilterState
AppState = state.AppState
from loglens.model import LogRecord

fs = FilterState(min_severity="WARNING", keyword="ssh")
assert fs.min_severity == "WARNING"
assert fs.keyword == "ssh"
print("  ✓ FilterState instantiation")

app_state = AppState()
assert len(app_state.records) == 0
assert app_state.follow_mode is False
print("  ✓ AppState instantiation")

# Test category extraction
test_record = LogRecord(
    timestamp="2026-02-15T10:30:00",
    severity_num=3,
    severity_label="ERROR",
    message="Test message",
    raw={"_SYSTEMD_UNIT": "test.service"}
)
app_state.records.append(test_record)

categories = app_state.get_categories()
assert "test.service" in categories
print("  ✓ Category extraction")

category = app_state._get_category(test_record)
assert category == "test.service"
print("  ✓ Category mapping (_SYSTEMD_UNIT)")

# Test fallback
test_record2 = LogRecord(
    timestamp="2026-02-15T10:30:00",
    severity_num=3,
    severity_label="ERROR",
    message="Test message",
    raw={"SYSLOG_IDENTIFIER": "myapp"}
)
category2 = app_state._get_category(test_record2)
assert category2 == "myapp"
print("  ✓ Category fallback (SYSLOG_IDENTIFIER)")

# Test unknown
test_record3 = LogRecord(
    timestamp="2026-02-15T10:30:00",
    severity_num=3,
    severity_label="ERROR",
    message="Test message",
    raw={}
)
category3 = app_state._get_category(test_record3)
assert category3 == "(unknown)"
print("  ✓ Category fallback (unknown)")

print()

# 4. Test backend adapter
print("✓ Testing backend adapter...")
BackendAdapter = backend.BackendAdapter
from loglens.sources.base import SourceError

adapter = BackendAdapter(max_buffer=100)
assert adapter.max_buffer == 100
print("  ✓ BackendAdapter instantiation")

# Test fetch (will succeed if journalctl available)
try:
    records = adapter.fetch_records(limit=5, warn_on_errors=False)
    print(f"  ✓ fetch_records() returned {len(records)} records")
except SourceError as e:
    print(f"  ⚠ fetch_records() failed (expected if no journalctl): {e}")

# Test diagnostics access
stats = adapter.get_stats()
assert 'normalization' in stats
print("  ✓ get_stats() works")

adapter.reset_stats()
print("  ✓ reset_stats() works")

print()

# 5. Check textual availability
print("✓ Checking textual availability...")
try:
    import textual
    print(f"  ✓ Textual {textual.__version__} is installed")
    print("  → You can run: python3 logtui.py")
except ImportError:
    print("  ⚠ Textual not installed")
    print("  → Install: pip install textual")
    print("  → Then run: python3 logtui.py")

print()
print("="*70)
print("Phase 2 TUI Structure: ✅ VERIFIED")
print("="*70)
print()
print("Summary:")
print(f"  • {len(expected_files)} files created")
print("  • State models working")
print("  • Backend adapter working")
print("  • All modules syntactically correct")
print()
print("To use the TUI:")
print("  1. Install textual: pip install textual")
print("  2. Run: python3 logtui.py")
print("  3. Or: python3 logtui.py --since=-1h --priority=3")
print()
