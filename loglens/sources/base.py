"""
Base interface for log sources.

Any log source (journalctl, files, Docker, etc.) implements LogSource.
"""

from abc import ABC, abstractmethod
from typing import Iterator

from ..model import RawEvent


class LogSource(ABC):
    """
    Abstract base class for log sources.
    
    A log source reads from some input (journal, file, remote API, etc.)
    and yields RawEvent objects that can be normalized into LogRecords.
    """
    
    @abstractmethod
    def read(self) -> Iterator[RawEvent]:
        """
        Read log entries from the source.
        
        Yields:
            RawEvent objects containing raw log data
            
        Raises:
            SourceError: If the source cannot be read
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Clean up resources (file handles, processes, etc.).
        
        Should be idempotent and safe to call multiple times.
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


class SourceError(Exception):
    """Base exception for log source errors."""
    pass


class SourceNotFoundError(SourceError):
    """Raised when a required source tool/file is not available."""
    pass


class SourcePermissionError(SourceError):
    """Raised when access to source is denied."""
    pass
