"""
Main screen for LogLens TUI - 3-pane layout.

Layout:
┌─────────────────────────────────────────────────┐
│ Filter Bar (search, severity, actions)          │
├──────────┬────────────────────────┬──────────────┤
│ Sidebar  │ Log Table              │ Details      │
│          │                        │ Panel        │
│ [Units/  │ [Timestamp | Severity  │              │
│  Apps]   │  | Message]            │ [Selected    │
│          │                        │  log curated │
│          │                        │  or raw]     │
└──────────┴────────────────────────┴──────────────┘
│ Status Bar                                       │
└──────────────────────────────────────────────────┘
"""

import json
from datetime import datetime
from textual.app import ComposeResult
from textual.screen import Screen
from textual.message import Message
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header, Footer, DataTable, Static, Input, 
    Button, ListView, ListItem, Label
)
from textual.binding import Binding
from loglens.model import LogRecord
from loglens.tui.state import AppState, FilterState


class LogTable(DataTable):
    """Log entries table widget."""
    pass


class CategorySidebar(ListView):
    """Sidebar showing systemd units/apps."""
    can_focus = True


class DetailsPanel(VerticalScroll):
    """Details panel showing selected log record."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record: LogRecord | None = None
        self.show_raw: bool = False
    
    def update_record(self, record: LogRecord | None, show_raw: bool = False):
        """Update the displayed record."""
        self.record = record
        self.show_raw = show_raw
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the panel content."""
        self.remove_children()
        
        if not self.record:
            self.mount(Static("No log selected", classes="detail-empty"))
            return
        
        if self.show_raw:
            # Show raw JSON
            raw_json = json.dumps(self.record.raw or {}, indent=2)
            self.mount(Static(f"[bold]Raw Event Data:[/bold]\n\n{raw_json}", classes="detail-raw"))
        else:
            # Show curated view
            lines = []
            
            # Format timestamp to local time
            ts_display = self.record.timestamp
            if isinstance(ts_display, str):
                try:
                    dt = datetime.fromisoformat(ts_display.replace('Z', '+00:00'))
                    dt_local = dt.astimezone()
                    ts_display = dt_local.strftime("%Y-%m-%d %H:%M:%S %Z")
                except:
                    pass  # Use original string if parsing fails
            
            lines.append(f"[bold]Timestamp:[/bold] {ts_display}")
            lines.append(f"[bold]Severity:[/bold] {self.record.severity_label} ({self.record.severity_num})")
            lines.append(f"[bold]Message:[/bold]\n{self.record.message}")
            
            # Show common fields from raw
            if self.record.raw:
                lines.append("\n[bold]Additional Fields:[/bold]")
                
                common_fields = [
                    '_SYSTEMD_UNIT', 'SYSLOG_IDENTIFIER', '_COMM',
                    '_PID', '_UID', '_GID', '_HOSTNAME', '_BOOT_ID'
                ]
                
                for field in common_fields:
                    value = self.record.raw.get(field)
                    if value:
                        lines.append(f"  {field}: {value}")
            
            content = "\n".join(lines)
            self.mount(Static(content, classes="detail-curated"))


class StatsBar(Static):
    """Statistics bar showing log counts and status."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_logs = 0
        self.follow_active = False
    
    def update_stats(self, total: int, follow: bool = False):
        """Update the stats display."""
        self.total_logs = total
        self.follow_active = follow
        
        follow_indicator = "[green]●[/green] FOLLOW ON" if follow else "○ Follow Off"
        self.update(f"📊 Total Logs: {total} | {follow_indicator}")


class FilterBar(Horizontal):
    """Filter controls bar."""
    
    def compose(self) -> ComposeResult:
        yield Input(placeholder="🔍 Search keyword...", id="search-input")
        yield Input(placeholder="⚠️  Min severity (e.g. WARNING)", id="severity-input")
        yield Button("Reload", id="reload-btn", variant="primary")
        yield Button("Follow", id="follow-btn")
        yield Button("Toggle Raw", id="toggle-raw-btn")


class MainScreen(Screen):
    """Main application screen with 3-pane layout."""
    
    # Severity color mapping (Rich markup)
    SEVERITY_COLORS = {
        "EMERG": "bright_magenta",
        "ALERT": "bright_red",
        "CRIT": "red",
        "ERROR": "red",
        "WARNING": "yellow",
        "NOTICE": "cyan",
        "INFO": "green",
        "DEBUG": "dim white",
    }
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "reload", "Reload"),
        Binding("ctrl+f", "toggle_follow", "Toggle Follow"),
        Binding("ctrl+t", "toggle_raw", "Toggle Raw/Curated"),
        Binding("ctrl+s", "focus_search", "Focus Search"),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Prev", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("left", "focus_sidebar", "Sidebar", show=False),
        Binding("right", "focus_table", "Table", show=False),
    ]
    
    def __init__(self, app_state: AppState, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_state = app_state
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield StatsBar(id="stats-bar", classes="stats-bar")
        yield FilterBar(classes="filter-bar")
        
        with Horizontal(id="main-container"):
            # Sidebar: 20% width
            with Vertical(id="sidebar", classes="pane"):
                yield Label("Categories", classes="sidebar-header")
                yield CategorySidebar(id="category-list")
            
            # Log table: 50% width
            with Vertical(id="table-container", classes="pane"):
                table = LogTable(id="log-table")
                table.add_columns("Timestamp", "Severity", "Message")
                table.cursor_type = "row"
                yield table
            
            # Details panel: 30% width
            with Vertical(id="details-container", classes="pane"):
                yield Label("Details", classes="details-header")
                yield DetailsPanel(id="details-panel")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Handle screen mount."""
        self.update_sidebar()
        self.update_table()
        self.update_stats()
        self.update_status()
        
        # Set initial focus to table
        table = self.query_one("#log-table", LogTable)
        table.focus()
    
    def update_sidebar(self):
        """Update sidebar categories from app state."""
        sidebar = self.query_one("#category-list", CategorySidebar)
        sidebar.clear()
        
        categories = self.app_state.get_categories()
        
        for category in categories:
            sidebar.append(ListItem(Label(category)))
    
    def update_stats(self):
        """Update stats bar."""
        stats_bar = self.query_one("#stats-bar", StatsBar)
        stats_bar.update_stats(
            total=len(self.app_state.records),
            follow=self.app_state.follow_mode
        )
    
    def update_table(self):
        """Update log table from app state."""
        table = self.query_one("#log-table", LogTable)
        table.clear()
        
        # Apply filters
        filtered_records = self.app_state.apply_filters()
        
        for record in filtered_records:
            # Format timestamp - convert from UTC to local time
            ts = record.timestamp
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    # Convert to local timezone
                    dt_local = dt.astimezone()
                    ts_display = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    ts_display = ts[:19] if len(ts) > 19 else ts
            else:
                ts_display = str(ts)
            
            # Apply color to severity label
            color = self.SEVERITY_COLORS.get(record.severity_label, "white")
            severity_colored = f"[{color}]{record.severity_label}[/{color}]"
            
            # Truncate message
            msg = record.message[:80] + "..." if len(record.message) > 80 else record.message
            
            table.add_row(ts_display, severity_colored, msg)
    
    def update_details(self):
        """Update details panel for selected row."""
        table = self.query_one("#log-table", LogTable)
        details = self.query_one("#details-panel", DetailsPanel)
        
        if table.cursor_row < len(self.app_state.records):
            filtered = self.app_state.apply_filters()
            if table.cursor_row < len(filtered):
                record = filtered[table.cursor_row]
                details.update_record(record, self.app_state.show_raw_details)
                return
        
        details.update_record(None)
    
    def update_status(self):
        """Update status bar message."""
        status = self.app_state.status_message
        if self.app_state.error_message:
            status = f"ERROR: {self.app_state.error_message}"
        
        # Status is shown in Footer automatically
        # We could add a dedicated status widget if needed
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in log table."""
        self.update_details()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle category selection in sidebar."""
        sidebar = self.query_one("#category-list", CategorySidebar)
        
        if sidebar.index is not None:
            categories = self.app_state.get_categories()
            if sidebar.index < len(categories):
                selected = categories[sidebar.index]
                
                # Update filter state
                if self.app_state.filters.category == selected:
                    # Deselect
                    self.app_state.filters.category = None
                else:
                    # Select
                    self.app_state.filters.category = selected
                
                # Refresh table
                self.update_table()
                self.update_stats()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "reload-btn":
            self.action_reload()
        elif event.button.id == "follow-btn":
            self.action_toggle_follow()
        elif event.button.id == "toggle-raw-btn":
            self.action_toggle_raw()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input field submissions."""
        if event.input.id == "search-input":
            self.app_state.filters.keyword = event.value or None
            self.action_reload()
        elif event.input.id == "severity-input":
            self.app_state.filters.min_severity = event.value or None
            self.action_reload()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_reload(self) -> None:
        """Reload logs from backend."""
        self.app_state.status_message = "Reloading..."
        self.update_status()
        
        # Trigger reload in app
        self.app.post_message(self.ReloadRequested())
    
    def action_toggle_follow(self) -> None:
        """Toggle follow mode."""
        self.app_state.follow_mode = not self.app_state.follow_mode
        follow_btn = self.query_one("#follow-btn", Button)
        follow_btn.variant = "success" if self.app_state.follow_mode else "default"
        
        self.app_state.status_message = f"Follow mode: {'ON' if self.app_state.follow_mode else 'OFF'}"
        self.update_stats()
        self.update_status()
        
        # If follow mode enabled, trigger immediate reload
        if self.app_state.follow_mode:
            self.action_reload()
    
    def action_toggle_raw(self) -> None:
        """Toggle raw/curated details view."""
        self.app_state.show_raw_details = not self.app_state.show_raw_details
        self.update_details()
    
    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
    
    def action_cursor_up(self) -> None:
        """Move table cursor up."""
        table = self.query_one("#log-table", LogTable)
        table.action_cursor_up()
    
    def action_cursor_down(self) -> None:
        """Move table cursor down."""
        table = self.query_one("#log-table", LogTable)
        table.action_cursor_down()
    
    def action_focus_sidebar(self) -> None:
        """Focus the sidebar."""
        sidebar = self.query_one("#category-list", CategorySidebar)
        sidebar.focus()
    
    def action_focus_table(self) -> None:
        """Focus the log table."""
        table = self.query_one("#log-table", LogTable)
        table.focus()
    
    class ReloadRequested(Message):
        """Message to request reload from app."""
        pass
