# Phase 2: LogLens TUI

## Overview

Phase 2 implements a Textual-based Terminal User Interface (TUI) for viewing and filtering logs interactively.

## Architecture

```
loglens/tui/
├── __init__.py          # Package exports
├── app.py               # Main application class
├── app.css              # Dark theme styling
├── state.py             # UI state models (FilterState, AppState)
├── backend.py           # Backend adapter layer
└── screens/
    ├── __init__.py
    └── main.py          # Main 3-pane screen
```

## Design Principles

1. **Strict Separation**: No backend logic in UI layer
   - All log processing happens in `loglens.engine`
   - TUI only orchestrates and displays

2. **Pluggable Architecture**: Works with any log source
   - Backend adapter handles iterator → list conversion
   - Source switching transparent to UI

3. **3-Pane Layout**:
   ```
   ┌─────────────────────────────────────────────┐
   │ Filter Bar                                  │
   ├──────────┬──────────────────┬───────────────┤
   │ Sidebar  │ Log Table        │ Details       │
   │ (Units)  │ (Timestamp/Sev)  │ (Curated/Raw) │
   └──────────┴──────────────────┴───────────────┘
   │ Status Bar                                  │
   └─────────────────────────────────────────────┘
   ```

## Installation

### Requirements

- Python 3.10+
- Textual 0.50.0+

### Install Textual

```bash
# Using pip (if available)
pip install textual

# Or using system package manager
# Ubuntu/Debian:
sudo apt install python3-textual

# Arch:
sudo pacman -S python-textual
```

## Usage

### Command-Line Interface

```bash
# Basic usage
python3 logtui.py

# View last hour
python3 logtui.py --since=-1h

# Filter by systemd unit
python3 logtui.py --units=sshd.service nginx.service

# View file-based logs
python3 logtui.py --file=/var/log/syslog

# Filter by priority (0=EMERG to 7=DEBUG)
python3 logtui.py --priority=3  # ERROR and above
```

### Programmatic API

```python
from loglens.tui.app import run_tui

# Run with default settings
run_tui()

# Run with custom source
run_tui(source="journalctl", since="-1h", units=["sshd.service"])

# Run with file source
run_tui(source="file", path="/var/log/syslog", mode="text")
```

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit application |
| `Ctrl+R` | Reload logs |
| `Ctrl+F` | Toggle follow mode (journalctl only) |
| `Ctrl+T` | Toggle raw/curated details view |
| `Ctrl+S` | Focus search input |
| `↑/↓` | Navigate table rows |
| `←/→` | Switch between sidebar and table |
| `Enter` | Submit search/filter |

## Features

### Sidebar Categories

Shows unique systemd units and applications extracted from logs:
- Priority: `_SYSTEMD_UNIT` → `SYSLOG_IDENTIFIER` → `(unknown)`
- Click to filter by category
- Click again to deselect

### Hybrid Filtering

- **In-memory**: Fast category filtering on loaded records
- **Backend reload**: Keyword/severity filters trigger backend fetch
- Best of both: instant sidebar clicks + thorough backend searches

### Details Panel

Two modes (toggle with `Ctrl+T`):

1. **Curated View**: Human-readable format
   - Timestamp, severity, message
   - Common fields: unit, PID, host, etc.

2. **Raw View**: Complete JSON dump
   - All fields from source
   - Useful for debugging/inspection

### Follow Mode

Real-time log streaming (journalctl only):
- Toggle with `Ctrl+F` or "Follow" button
- Continuously fetches new logs
- Auto-scrolls to latest entries

### Performance Guardrails

- Ring buffer: Max 10,000 records in memory
- Batch UI updates: Prevents UI freezing
- Truncated messages: Long messages abbreviated in table

## Error Handling

- Invalid sources: Clear error messages in status bar
- Parsing failures: Tracked in diagnostics (available in backend)
- Missing fields: Graceful fallbacks to "(unknown)"

## Testing Without Textual

Phase 1 backend is fully independent:

```python
# Phase 1 works without textual
from loglens import fetch_logs, filter_logs

logs = list(fetch_logs(limit=10))
filtered = filter_logs(logs, min_severity="WARNING")
```

## Development

### Syntax Check

```bash
# Verify TUI code parses correctly
python3 -m py_compile loglens/tui/*.py loglens/tui/screens/*.py
```

### Manual Testing

Once textual is installed:

```bash
# Basic launch
python3 logtui.py

# Test filtering
python3 logtui.py --since=-5m --priority=4

# Test file mode
python3 logtui.py --file=demo_logs.txt
```

## Limitations

1. **Follow mode**: Journalctl only (file follow not implemented)
2. **Buffer cap**: 10,000 records max in memory
3. **No export**: Cannot export filtered logs to file (future enhancement)
4. **Single source**: Cannot mix multiple sources in one view

## Future Enhancements

- Export filtered logs to file
- Multiple tabs for different sources
- Live search (debounced)
- Column sorting
- Log level color coding
- Bookmarking/highlighting
- Search history

## Troubleshooting

### "ModuleNotFoundError: No module named 'textual'"

Install textual: `pip install textual`

### "SourceError: journalctl not found"

Ensure systemd is installed and `journalctl` is in PATH.

### UI appears corrupted

- Terminal too small: Minimum 80x24 recommended
- Terminal emulator: Use modern terminal (e.g., GNOME Terminal, Alacritty)

### Follow mode not working

- Only works with journalctl source
- Requires sudo/proper permissions for `journalctl -f`

## Phase Completion

✅ All Phase 2 requirements implemented:
- 3-pane layout with sidebar, table, details
- Dark professional theme
- Sidebar shows systemd units/apps
- Hybrid filtering (in-memory + reload)
- Keyboard navigation
- Follow mode (journalctl only)
- Detail panel with curated/raw toggle
- Error handling UI
- Entry script with CLI options
- Performance guardrails
- Strict backend separation maintained
