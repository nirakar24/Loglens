"""Tests for source registry."""

import pytest
from loglens.sources.registry import (
    register_source,
    get_source,
    list_sources,
    _clear_registry,
)
from loglens.sources.base import LogSource
from loglens.model import RawEvent


class FakeSource(LogSource):
    """Fake source for testing."""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.closed = False
    
    def read(self):
        yield RawEvent(data={"test": "data"}, source_type="fake")
    
    def close(self):
        self.closed = True


class TestSourceRegistry:
    def setup_method(self):
        """Clear registry before each test."""
        _clear_registry()
    
    def test_register_and_get_source(self):
        """Test registering and retrieving a source."""
        register_source("fake", FakeSource)
        
        source = get_source("fake")
        assert isinstance(source, FakeSource)
    
    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate name raises error."""
        register_source("fake", FakeSource)
        
        with pytest.raises(ValueError, match="already registered"):
            register_source("fake", FakeSource)
    
    def test_get_unknown_source_raises_error(self):
        """Test that getting unknown source raises KeyError."""
        with pytest.raises(KeyError, match="Unknown source"):
            get_source("nonexistent")
    
    def test_get_source_with_kwargs(self):
        """Test that kwargs are passed to source constructor."""
        register_source("fake", FakeSource)
        
        source = get_source("fake", custom_arg="value", another=123)
        assert source.kwargs["custom_arg"] == "value"
        assert source.kwargs["another"] == 123
    
    def test_list_sources(self):
        """Test listing all registered sources."""
        _clear_registry()
        
        register_source("source1", FakeSource)
        register_source("source2", FakeSource)
        register_source("source3", FakeSource)
        
        sources = list_sources()
        assert sources == ["source1", "source2", "source3"]
    
    def test_list_sources_empty(self):
        """Test listing sources when registry is empty."""
        _clear_registry()
        assert list_sources() == []


class TestBuiltInSources:
    def test_journalctl_registered(self):
        """Test that journalctl source is registered by default."""
        from loglens.sources import list_sources
        assert "journalctl" in list_sources()
    
    def test_file_registered(self):
        """Test that file source is registered by default."""
        from loglens.sources import list_sources
        assert "file" in list_sources()
