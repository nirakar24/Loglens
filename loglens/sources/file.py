"""
File-based log source for reading log files.

Supports plain text line-based logs and JSON Lines (NDJSON) format.
Future parsers (nginx, syslog, Docker, etc.) can be added here.
"""

import json
from pathlib import Path
from typing import Iterator, Literal, Optional

from .base import LogSource, SourceError, SourceNotFoundError
from ..model import RawEvent


class FileSource(LogSource):
    """
    Log source that reads from local files.
    
    Args:
        path: Path to log file
        mode: Format mode - "text" for line-based text, "jsonl" for JSON Lines
        encoding: File encoding. Defaults to utf-8.
        follow: If True, continuously tail new entries (not yet implemented). Default False.
    """
    
    def __init__(
        self,
        path: str,
        mode: Literal["text", "jsonl"] = "text",
        encoding: str = "utf-8",
        follow: bool = False,
    ):
        self.path = Path(path)
        self.mode = mode
        self.encoding = encoding
        self.follow = follow
        self._file: Optional[object] = None
        
        if follow:
            raise NotImplementedError("Follow mode not yet implemented for file sources")
    
    def read(self) -> Iterator[RawEvent]:
        """
        Read log entries from file.
        
        Yields:
            RawEvent objects with either text lines or JSON dicts
            
        Raises:
            SourceNotFoundError: If file does not exist
            SourceError: For read errors
        """
        if not self.path.exists():
            raise SourceNotFoundError(f"File not found: {self.path}")
        
        if not self.path.is_file():
            raise SourceError(f"Not a file: {self.path}")
        
        try:
            with open(self.path, "r", encoding=self.encoding) as f:
                self._file = f
                
                for line_num, line in enumerate(f, start=1):
                    line = line.rstrip("\n\r")
                    
                    if not line:
                        # Skip empty lines
                        continue
                    
                    if self.mode == "jsonl":
                        try:
                            data = json.loads(line)
                            yield RawEvent(
                                data=data,
                                source_type="file_jsonl",
                                metadata={"path": str(self.path), "line": line_num}
                            )
                        except json.JSONDecodeError as e:
                            # Skip malformed JSON lines but continue processing
                            # In production, consider logging these errors
                            continue
                    else:  # text mode
                        yield RawEvent(
                            data=line,
                            source_type="file_text",
                            metadata={"path": str(self.path), "line": line_num}
                        )
        
        except PermissionError as e:
            raise SourceError(f"Permission denied reading {self.path}: {e}")
        except UnicodeDecodeError as e:
            raise SourceError(
                f"Failed to decode {self.path} with encoding '{self.encoding}': {e}"
            )
        except OSError as e:
            raise SourceError(f"Failed to read {self.path}: {e}")
        finally:
            self._file = None
    
    def close(self) -> None:
        """Close file handle if open."""
        # File is closed automatically by context manager in read()
        # This method is here for interface compliance
        pass
