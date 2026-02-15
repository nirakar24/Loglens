# LogLens - Linux Log Viewer

A powerful Linux log processing engine with an interactive Terminal UI for viewing and analyzing system logs. Think of it as a Linux equivalent to Windows Event Viewer.

## Features

### 🚀 Core Engine
- **Pluggable Sources**: Extensible architecture for different log sources
  - `journalctl` (systemd journal) - fully implemented
  - File-based logs (text & JSON Lines)
  - Easy to add: Docker, nginx, remote syslog, cloud APIs
  
- **Structured Output**: Normalized `LogRecord` objects with:
  - ISO-8601 timestamps (auto-converted to local timezone)
  - Severity numbers (0-7) and labels (EMERG, ALERT, CRIT, ERROR, WARNING, NOTICE, INFO, DEBUG)
  - Message content
  - Raw data preservation for debugging

- **Powerful Filtering**:
  - Exact severity match
  - Minimum severity threshold (e.g., "WARNING and above")
  - Keyword search (case-sensitive or insensitive)
  - Combinable filters with AND logic

### 🖥️ Interactive TUI
- **3-Pane Layout**: Categories sidebar | Log table | Details panel
- **Color-Coded Severity Levels**: Instantly spot critical issues
  - EMERG/ALERT: Bright red/magenta
  - ERROR: Red
  - WARNING: Yellow
  - INFO: Green
  - DEBUG: Dim
- **Real-Time Filtering**: Click categories in sidebar for instant filtering
- **Dual Details View**: Toggle between curated (human-readable) and raw (full JSON)
- **Time Range Queries**: Filter logs by time with no memory limits when `--since` is used
- **Latest-First Sorting**: Most recent logs always on top
- **Keyboard Navigation**: Full keyboard control for efficient workflow

## Installation

### Requirements
- Python 3.10+
- systemd (for journalctl support)
- Textual 0.50.0+ (for TUI)

### Install

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: For TUI interface
pip install textual
```

## Quick Start

### TUI (Terminal User Interface)

```bash
# View recent logs
python3 logtui.py

# View logs from last 5 days (no limit)
python3 logtui.py --since="5 days ago"

# Filter by severity
python3 logtui.py --priority=3    # ERROR and above

# Filter by systemd unit
python3 logtui.py --units=sshd.service nginx.service

# View file-based logs
python3 logtui.py --file=/var/log/syslog
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit |
| `Ctrl+R` | Reload logs |
| `Ctrl+F` | Toggle follow mode |
| `Ctrl+T` | Toggle raw/curated details |
| `Ctrl+S` | Focus search |
| `↑/↓` | Navigate rows |
| `Tab` | Switch focus |
| `Enter` | Apply search/filter |

### Programmatic API

```python
from loglens import fetch_logs, filter_logs

# Fetch all logs from last 24 hours (default)
for record in fetch_logs():
    print(f"{record.timestamp} [{record.severity_label}] {record.message}")

# Fetch and filter errors
logs = fetch_logs(source="journalctl")
errors = filter_logs(logs, min_severity="error")
for record in errors:
    print(f"ERROR: {record.message}")

# Custom time range
logs = fetch_logs(
    source="journalctl",
    since="2026-02-10 00:00:00",
    units=["nginx.service"]
)

# Keyword filtering
for record in filter_logs(logs, keyword="timeout"):
    print(record.message)

# Read from files
logs = fetch_logs(source="file", path="/var/log/app.log", mode="text")
for record in logs:
    print(record.message)

# Combine fetch and filter
from loglens import fetch_and_filter_logs

critical = fetch_and_filter_logs(
    source="journalctl",
    since="-1h",
    min_severity="error",
    keyword="failed"
)
```

## Architecture

```
loglens/
├── model.py           # Data models (LogRecord, RawEvent)
├── severity.py        # Severity mapping utilities
├── normalize.py       # Event normalization layer
├── filtering.py       # Filtering logic
├── engine.py          # Public API
├── sources/           # Pluggable log sources
│   ├── base.py        # LogSource protocol
│   ├── registry.py    # Source registration system
│   ├── journalctl.py  # Systemd journal source
│   └── file.py        # File-based source
└── tui/               # Terminal UI
    ├── app.py         # Main application
    ├── app.css        # Dark theme styling
    ├── state.py       # UI state management
    ├── backend.py     # Backend adapter layer
    └── screens/
        └── main.py    # Main 3-pane screen

logtui.py              # TUI entry point
tests/                 # Comprehensive test suite
```

## Design Principles

1. **Strict Separation**: Backend engine has no UI dependencies
   - Use programmatically in any context (CLI, web service, scripts)
   - TUI is a separate layer that orchestrates the engine

2. **Streaming Architecture**: Iterators throughout for memory efficiency
   - Handle massive log volumes
   - No limit when using `--since` time ranges

3. **Pluggable & Extensible**: Easy to add new sources
   - Docker logs, nginx logs, remote syslog
   - Custom parsers for any log format

4. **Type Safety**: Structured models with full validation

5. **Performance**: 
   - Lazy evaluation with iterators
   - Smart buffering (10k cap by default, unlimited with time ranges)
   - Efficient UI updates

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=loglens --cov-report=html

# Run specific test file
pytest tests/test_engine.py -v
```

### Code Structure

- **Backend Engine** (`loglens/`): Pure Python, no UI dependencies
- **TUI Layer** (`loglens/tui/`): Textual-based interface
- **Entry Point** (`logtui.py`): Command-line launcher
- **Tests** (`tests/`): Comprehensive test suite

### Adding New Log Sources

Implement the `LogSource` protocol and register it:

```python
from loglens.sources.base import LogSource
from loglens.sources.registry import register_source
from loglens.model import RawEvent

class MyCustomSource(LogSource):
    def __init__(self, **kwargs):
        # Initialize your source
        pass
    
    def read(self):
        # Yield RawEvent objects
        for entry in my_data_source:
            yield RawEvent(
                data=entry,
                source_type="custom",
                metadata={}
            )
    
    def close(self):
        # Cleanup
        pass

# Register it
register_source("custom", MyCustomSource)

# Use it
from loglens import fetch_logs
logs = fetch_logs(source="custom", my_param="value")
```

## Examples

### Analyze Failed SSH Logins

```bash
python3 logtui.py --units=sshd.service --since="24 hours ago"
# Then press Ctrl+S and search for "failed"
```

### Monitor System Errors in Real-Time

```bash
python3 logtui.py --priority=3 --since="now"
# Press Ctrl+F to enable follow mode
```

### Export Errors to Script

```python
from loglens import fetch_and_filter_logs

errors = fetch_and_filter_logs(
    source="journalctl",
    since="-24h",
    min_severity="error"
)

with open("errors.txt", "w") as f:
    for record in errors:
        f.write(f"{record.timestamp} {record.message}\n")
```

### Find All Kernel Messages

```bash
# Launch TUI and use sidebar
python3 logtui.py --since="7 days ago"
# Click "kernel" in the Categories sidebar
```

## TUI Features in Detail

### Categories Sidebar
- Shows all unique categories from logs:
  - Systemd units (e.g., `sshd.service`, `nginx.service`)
  - Syslog identifiers (e.g., `kernel`, `sudo`, `systemd`)
- Click to filter instantly
- Click again to clear filter

### Severity Color Coding
- **EMERG/ALERT**: Bright magenta/red (system unusable)
- **CRIT/ERROR**: Red (critical errors)
- **WARNING**: Yellow (warnings)
- **NOTICE**: Cyan (normal but significant)
- **INFO**: Green (informational)
- **DEBUG**: Dim (debug messages)

### Details Panel
Toggle between two views with `Ctrl+T`:
- **Curated View**: Human-readable formatted display
  - Timestamp (local timezone)
  - Severity level
  - Message
  - Common fields (PID, UID, hostname, etc.)
- **Raw View**: Complete JSON dump for debugging

### Hybrid Filtering
- **In-Memory**: Category filtering (instant, no reload)
- **Backend Reload**: Keyword/severity filters (thorough search)

## Troubleshooting

### TUI Not Launching

```bash
# Install Textual
pip install textual

# Verify it's installed
python3 -c "import textual; print(textual.__version__)"
```

### Permission Denied (journalctl)

```bash
# Add user to systemd-journal group
sudo usermod -a -G systemd-journal $USER

# Log out and back in, or:
newgrp systemd-journal
```

### "journalctl not found"

LogLens requires systemd. If you're on a non-systemd system:
- Use file-based logs: `python3 logtui.py --file=/var/log/syslog`
- Or check if journalctl is in PATH

### No Logs Showing

- Check time range: `--since="7 days ago"` for more history
- Verify permissions: try `journalctl` directly in terminal
- Check filters: ensure priority/units are correct

### Search Input Not Visible (Known Issue)

This is a rendering issue with certain terminal configurations. Workaround:
- Type blindly in the search field (it still works)
- Or use CLI filters: `--priority=3` for errors

## Performance Notes

- **Default Mode**: Loads up to 1000 most recent logs (fast UI)
- **Time Range Mode**: When `--since` is used, loads all matching logs (no limit)
  - Use specific time ranges for large journals
  - Example: `--since="1 day ago"` instead of `--since="30 days ago"`
- **Memory Usage**: Proportional to logs loaded; sorted newest-first in memory

## Limitations

- Follow mode (`Ctrl+F`) is basic; full streaming not yet robust
- Cannot mix multiple log sources in one view
- No log export from TUI (use programmatic API for that)
- Search input visibility issues on some terminals

## Future Enhancements

- [ ] Export filtered logs from TUI
- [ ] Multiple tabs for different sources
- [ ] Live search with debouncing
- [ ] Column sorting
- [ ] Bookmarking/highlighting logs
- [ ] Search history
- [ ] Docker container logs source
- [ ] Kubernetes pod logs source
- [ ] nginx/Apache log parsers
- [ ] Remote syslog support

## Contributing

LogLens uses a clean, extensible architecture. Contributions welcome for:
- New log sources (Docker, K8s, cloud providers)
- Log format parsers (nginx, Apache, app-specific)
- TUI enhancements
- Documentation improvements

## License

[Add your license here]

## Project Status

✅ **Phase 1 Complete**: Backend engine with pluggable sources  
✅ **Phase 2 Complete**: Interactive TUI with color coding and filtering  
🚀 **Production Ready**: Full-featured log viewer with programmatic API

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

