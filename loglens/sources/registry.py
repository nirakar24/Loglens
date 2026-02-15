"""
Registry for log source plugins.

Allows sources to be referenced by name (e.g., "journalctl", "file").
"""

from typing import Any, Callable, Dict, List, Type

from .base import LogSource


# Global registry: source_name -> constructor function/class
_SOURCES: Dict[str, Callable[..., LogSource]] = {}


def register_source(name: str, source_class: Type[LogSource]) -> None:
    """
    Register a log source implementation.
    
    Args:
        name: Name to register (e.g., "journalctl", "file")
        source_class: LogSource subclass or factory function
        
    Raises:
        ValueError: If name is already registered
    """
    if name in _SOURCES:
        raise ValueError(f"Source '{name}' is already registered")
    _SOURCES[name] = source_class


def get_source(name: str, **kwargs: Any) -> LogSource:
    """
    Get a log source instance by name.
    
    Args:
        name: Registered source name
        **kwargs: Arguments passed to source constructor
        
    Returns:
        Initialized LogSource instance
        
    Raises:
        KeyError: If source name is not registered
    """
    if name not in _SOURCES:
        available = ", ".join(sorted(_SOURCES.keys()))
        raise KeyError(
            f"Unknown source: '{name}'. Available sources: {available}"
        )
    source_class = _SOURCES[name]
    return source_class(**kwargs)


def list_sources() -> List[str]:
    """
    List all registered source names.
    
    Returns:
        Sorted list of source names
    """
    return sorted(_SOURCES.keys())


def _clear_registry() -> None:
    """Clear registry (for testing only)."""
    _SOURCES.clear()
