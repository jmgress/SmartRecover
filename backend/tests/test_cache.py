"""Tests for agent caching functionality."""
import pytest
import time
from backend.cache import AgentCache


def test_cache_initialization():
    """Test cache initialization with default TTL."""
    cache = AgentCache(default_ttl=300)
    assert cache.default_ttl == 300


def test_cache_set_and_get():
    """Test setting and getting cache entries."""
    cache = AgentCache()
    test_data = {"key": "value", "numbers": [1, 2, 3]}
    
    cache.set("incident-1", test_data)
    result = cache.get("incident-1")
    
    assert result is not None
    assert result == test_data


def test_cache_miss():
    """Test cache miss for non-existent key."""
    cache = AgentCache()
    result = cache.get("non-existent")
    
    assert result is None


def test_cache_expiry():
    """Test that cache entries expire after TTL."""
    cache = AgentCache(default_ttl=1)  # 1 second TTL
    test_data = {"key": "value"}
    
    cache.set("incident-1", test_data)
    
    # Should be available immediately
    result = cache.get("incident-1")
    assert result is not None
    
    # Wait for expiry
    time.sleep(1.5)
    
    # Should be expired now
    result = cache.get("incident-1")
    assert result is None


def test_cache_custom_ttl():
    """Test setting custom TTL for cache entries."""
    cache = AgentCache(default_ttl=300)
    test_data = {"key": "value"}
    
    cache.set("incident-1", test_data, ttl=1)  # Override with 1 second
    
    # Should be available immediately
    result = cache.get("incident-1")
    assert result is not None
    
    # Wait for expiry
    time.sleep(1.5)
    
    # Should be expired now
    result = cache.get("incident-1")
    assert result is None


def test_cache_invalidate():
    """Test manual cache invalidation."""
    cache = AgentCache()
    test_data = {"key": "value"}
    
    cache.set("incident-1", test_data)
    assert cache.get("incident-1") is not None
    
    cache.invalidate("incident-1")
    assert cache.get("incident-1") is None


def test_cache_clear():
    """Test clearing all cache entries."""
    cache = AgentCache()
    
    cache.set("incident-1", {"data": 1})
    cache.set("incident-2", {"data": 2})
    cache.set("incident-3", {"data": 3})
    
    assert cache.get("incident-1") is not None
    assert cache.get("incident-2") is not None
    assert cache.get("incident-3") is not None
    
    cache.clear()
    
    assert cache.get("incident-1") is None
    assert cache.get("incident-2") is None
    assert cache.get("incident-3") is None


def test_cache_cleanup_expired():
    """Test cleanup of expired entries."""
    cache = AgentCache(default_ttl=1)
    
    cache.set("incident-1", {"data": 1})
    cache.set("incident-2", {"data": 2}, ttl=10)  # This one won't expire
    
    # Wait for first entry to expire
    time.sleep(1.5)
    
    cache.cleanup_expired()
    
    # First should be gone, second should remain
    assert cache.get("incident-1") is None
    assert cache.get("incident-2") is not None


def test_cache_thread_safety():
    """Test that cache operations are thread-safe."""
    import threading
    
    cache = AgentCache()
    results = []
    
    def set_cache(incident_id: str, data: dict):
        cache.set(incident_id, data)
        results.append(f"set-{incident_id}")
    
    def get_cache(incident_id: str):
        result = cache.get(incident_id)
        if result:
            results.append(f"get-{incident_id}")
    
    # Create multiple threads
    threads = []
    for i in range(10):
        t1 = threading.Thread(target=set_cache, args=(f"incident-{i}", {"data": i}))
        t2 = threading.Thread(target=get_cache, args=(f"incident-{i}",))
        threads.extend([t1, t2])
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    # Verify all set operations completed
    assert len([r for r in results if r.startswith("set-")]) == 10
