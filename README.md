# LogLens - Linux Log Processing Engine

A clean, pluggable backend for fetching, normalizing, and filtering Linux system logs.

## Phase 1: Backend Engine (Current)

LogLens provides a reusable log processing engine with no UI dependencies. It's designed to be the foundation for a Linux equivalent to Windows Event Viewer.

### Features

✅ **Pluggable Sources**: Extensible architecture for different log sources
- `journalctl` (systemd journal) - fully implemented
- File-based logs (text & JSON Lines) - skeleton ready for parsers

✅ **Structured Output**: Normalized `LogRecord` objects with:
- ISO-8601 timestamps
- Severity numbers (0-7) and labels (EMERG, ALERT, CRIT, ERROR, WARNING, NOTICE, INFO, DEBUG)
- Message content
- Optional raw data preservation

✅ **Flexible Filtering**:
- Exact severity match
- Minimum severity threshold (e.g., "WARNING and above")
- Keyword search (case-sensitive or insensitive)
- Combinable filters (AND logic)

✅ **Production-Ready Error Handling**:
- Graceful handling of missing `journalctl`
- Permission error detection
- Empty result sets
- Malformed log entries

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

### Quick Start

```python
from loglens import fetch_logs, filter_logs

# Fetch all logs from last 24 hours (default)
for record in fetch_logs():
    print(f"{record.timestamp} [{record.severity_label}] {record.message}")

# Fetch and filter errors only
logs = fetch_logs(source="journalctl")
errors = filter_logs(logs, min_severity="error")
for record in errors:
    print(f"ERROR: {record.message}")

# Fetch with custom time range
logs = fetch_logs(
    source="journalctl",
    since="2026-02-14 00:00:00",
    units=["nginx.service"]
)

# Filter by keyword
for record in filter_logs(logs, keyword="404"):
    print(record.message)

# Read from files
logs = fetch_logs(source="file", path="/var/log/app.log", mode="text")
for record in logs:
    print(record.message)
```

### Architecture

```
loglens/
├── model.py         # Data models (LogRecord, RawEvent)
├── severity.py      # Severity level mapping utilities
├── normalize.py     # Event normalization layer
├── filtering.py     # Filtering logic
├── engine.py        # Public API
└── sources/         # Pluggable log sources
    ├── base.py      # LogSource protocol
    ├── registry.py  # Source registration
    ├── journalctl.py
    └── file.py
```

### Design Principles

1. **No UI Dependency**: Pure backend, usable in any context (CLI, TUI, web service)
2. **Streaming First**: Iterators throughout to handle large log volumes
3. **Pluggable Sources**: Easy to add new log sources (Docker, nginx, syslog, remote, etc.)
4. **Separation of Concerns**: Source → Normalize → Filter → Output
5. **Type Safety**: Structured models with validation

### Success Criteria (Phase 1) ✅

- [x] `fetch_logs()` returns structured objects
- [x] `filter_logs()` works correctly
- [x] No UI dependency
- [x] Reusable log processing engine
- [x] Future-proofed for file-based logs

### Future-Proofing

The pluggable source architecture means adding support for new log types is straightforward:

**Want Docker logs?**
```python
# Just implement a DockerSource and register it
register_source("docker", DockerSource)
logs = fetch_logs(source="docker", container="app")
```

**Want nginx logs?**
```python
# Add an nginx parser to FileSource or create NginxSource
logs = fetch_logs(source="file", path="/var/log/nginx/access.log", mode="text")
# Parser can extract timestamp, method, status, etc. from the text
```

**Want remote logs?**
```python
register_source("ssh", SSHJournalSource)
logs = fetch_logs(source="ssh", host="remote.example.com")
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_engine.py -v
pytest tests/test_filtering.py -v

# Check coverage
pytest tests/ --cov=loglens --cov-report=html
```

## Phase 2: TUI Interface ✅

LogLens now includes a Textual-based Terminal User Interface for interactive log viewing!

### Quick Start

```bash
# Install textual (required for Phase 2)
pip install textual

# Launch TUI
python3 logtui.py

# Or with filters
python3 logtui.py --since=-1h --priority=3
```

### Features

- 🎨 **3-Pane Layout**: Sidebar (categories) | Log Table | Details Panel
- 🎯 **Smart Filtering**: Hybrid in-memory + backend reload
- ⚡ **Follow Mode**: Real-time log streaming (journalctl)
- 🔍 **Rich Details**: Toggle between curated and raw JSON view
- ⌨️ **Keyboard Navigation**: Full keyboard control
- 🌙 **Dark Theme**: Professional, easy-on-the-eyes interface

📖 **Full documentation**: See [PHASE2_README.md](PHASE2_README.md)

### Requirements

- Python 3.8+
- `systemd` (for journalctl source)
- `textual>=0.50.0` (for TUI, Phase 2 only)
- Optional: `pytest` for running tests

### License

MIT

## Contributing

This project is designed to be extensible. To add a new log source:

1. Implement `LogSource` interface in `loglens/sources/`
2. Register it in `engine.py`
3. Add normalizer logic in `normalize.py`
4. Add tests

See existing sources for examples.

