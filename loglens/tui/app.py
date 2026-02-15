"""
LogLens TUI Application.

Main application class managing screens, backend interactions, and lifecycle.
"""

from textual.app import App
from textual.reactive import reactive
from loglens.tui.state import AppState, FilterState
from loglens.tui.backend import BackendAdapter
from loglens.tui.screens.main import MainScreen
from loglens.sources.base import SourceError


class LogLensApp(App):
    """
    LogLens Textual Application.
    
    Manages:
    - UI screens and navigation
    - Backend adapter orchestration
    - Application state
    - Error handling
    """
    
    CSS_PATH = "app.css"
    TITLE = "LogLens - Log Viewer"
    
    def __init__(self, source: str = "journalctl", **kwargs):
        """
        Initialize LogLens app.
        
        Args:
            source: Log source type ('journalctl' or 'file')
            **kwargs: Additional source parameters
        """
        super().__init__()
        self.source = source
        self.source_kwargs = kwargs
        self.app_state = AppState()
        # If a time range is provided, avoid a fixed cap so users can page through
        # all logs within that time window.
        if kwargs.get("since"):
            self.backend = BackendAdapter(max_buffer=None)
        else:
            self.backend = BackendAdapter(max_buffer=10000)
    
    def on_mount(self) -> None:
        """Handle app mount - load initial data."""
        self.push_screen(MainScreen(self.app_state))
        self.load_logs()
    
    def load_logs(self):
        """Load logs from backend into app state."""
        try:
            self.app_state.error_message = None
            self.app_state.status_message = "Loading logs..."

            initial_limit = None if self.source_kwargs.get("since") else 1000
            
            # Fetch from backend
            records = self.backend.fetch_records(
                source=self.source,
                limit=initial_limit,
                follow=self.app_state.follow_mode,
                severity=self.app_state.filters.severity,
                min_severity=self.app_state.filters.min_severity,
                keyword=self.app_state.filters.keyword,
                case_sensitive=self.app_state.filters.case_sensitive,
                warn_on_errors=False,
                **self.source_kwargs
            )
            
            # Update state
            self.app_state.records = records
            self.app_state.status_message = f"Loaded {len(records)} logs"
            
            # Refresh UI
            self.refresh_ui()
        
        except SourceError as e:
            self.app_state.error_message = str(e)
            self.app_state.status_message = "Error loading logs"
            self.refresh_ui()
        
        except Exception as e:
            self.app_state.error_message = f"Unexpected error: {e}"
            self.app_state.status_message = "Error"
            self.refresh_ui()
    
    def refresh_ui(self):
        """Refresh all UI components."""
        try:
            screen = self.screen
            if isinstance(screen, MainScreen):
                screen.update_sidebar()
                screen.update_table()
                screen.update_details()
                screen.update_status()
        except Exception:
            pass  # Screen may not be ready
    
    def on_main_screen_reload_requested(self, event: MainScreen.ReloadRequested) -> None:
        """Handle reload request from main screen."""
        self.load_logs()


def run_tui(source: str = "journalctl", **kwargs):
    """
    Run the LogLens TUI application.
    
    Args:
        source: Log source type ('journalctl' or 'file')
        **kwargs: Additional source parameters (e.g., since, until, units, path, mode)
    
    Examples:
        >>> run_tui()  # Default journalctl
        >>> run_tui(source="file", path="/var/log/syslog", mode="text")
        >>> run_tui(source="journalctl", since="-1h", units=["ssh.service"])
    """
    app = LogLensApp(source=source, **kwargs)
    app.run()
