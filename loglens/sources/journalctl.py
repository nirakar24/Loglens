"""
Journalctl log source for systemd journal.

Reads logs from journalctl using JSON output format.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Iterator, Optional, List

from .base import LogSource, SourceError, SourceNotFoundError, SourcePermissionError
from ..model import RawEvent


class JournalctlSource(LogSource):
    """
    Log source that reads from systemd journal via journalctl.
    
    Args:
        since: Start time (ISO-8601 string or datetime). Defaults to 24 hours ago.
        until: End time (ISO-8601 string or datetime). Optional.
        units: List of systemd units to filter by. Optional.
        priority: Maximum priority level to include (0-7 or label). Optional.
        follow: If True, continuously tail new entries. Default False.
        warn_on_errors: If True, print warnings to stderr for skipped entries. Default True.
    """
    
    def __init__(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        units: Optional[List[str]] = None,
        priority: Optional[int] = None,
        follow: bool = False,
        warn_on_errors: bool = True,
    ):
        self.since = since or self._default_since()
        self.until = until
        self.units = units or []
        self.priority = priority
        self.follow = follow
        self.warn_on_errors = warn_on_errors
        self._process: Optional[subprocess.Popen] = None
        # Statistics
        self.stats = {
            "total_lines": 0,
            "empty_lines": 0,
            "json_errors": 0,
            "events_yielded": 0,
        }
    
    @staticmethod
    def _default_since() -> str:
        """Default to 24 hours ago."""
        dt = datetime.now() - timedelta(hours=24)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _build_command(self) -> List[str]:
        """Build journalctl command with arguments."""
        cmd = ["journalctl", "--output=json", "--no-pager"]
        
        # Time bounds
        cmd.extend(["--since", self.since])
        if self.until:
            cmd.extend(["--until", self.until])
        
        # Unit filters
        for unit in self.units:
            cmd.extend(["--unit", unit])
        
        # Priority filter
        if self.priority is not None:
            cmd.extend(["--priority", str(self.priority)])
        
        # Follow mode
        if self.follow:
            cmd.append("--follow")
        
        return cmd
    
    def read(self) -> Iterator[RawEvent]:
        """
        Read log entries from journalctl.
        
        Yields:
            RawEvent objects with journald JSON dicts
            
        Raises:
            SourceNotFoundError: If journalctl is not available
            SourcePermissionError: If access is denied
            SourceError: For other failures
        """
        cmd = self._build_command()
        
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
        except FileNotFoundError:
            raise SourceNotFoundError(
                "journalctl not found. Is systemd installed?"
            )
        
        try:
            assert self._process.stdout is not None
            for line in self._process.stdout:
                self.stats["total_lines"] += 1
                line = line.strip()
                if not line:
                    self.stats["empty_lines"] += 1
                    continue
                
                try:
                    data = json.loads(line)
                    self.stats["events_yielded"] += 1
                    yield RawEvent(
                        data=data,
                        source_type="journalctl",
                        metadata={"command": cmd}
                    )
                except json.JSONDecodeError as e:
                    # Skip malformed lines but track and warn
                    self.stats["json_errors"] += 1
                    if self.warn_on_errors:
                        print(f"Warning: Skipped malformed JSON line (total skipped: {self.stats['json_errors']})", 
                              file=sys.stderr)
                    continue
            
            # Wait for process to complete
            returncode = self._process.wait()
            
            # Check for errors
            if returncode != 0:
                stderr = self._process.stderr.read() if self._process.stderr else ""
                
                # Common error patterns
                if "permission denied" in stderr.lower() or "access denied" in stderr.lower():
                    raise SourcePermissionError(
                        f"Permission denied. Try: sudo usermod -a -G systemd-journal $USER\n{stderr}"
                    )
                elif returncode == 1 and not stderr.strip():
                    # journalctl returns 1 with no stderr when no entries found
                    # This is not an error
                    pass
                else:
                    raise SourceError(
                        f"journalctl exited with code {returncode}: {stderr}"
                    )
        
        except Exception:
            # Ensure process is terminated on any error
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            raise
    
    def close(self) -> None:
        """Terminate the journalctl process if running."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None
