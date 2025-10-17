"""
Test cache functionality with TTL jitter and prefix invalidation.
"""

import pytest
import time
from app.services.cache import cache_get, cache_set, cache_delete, cache_clear, cache_invalidate


def test_cache_basic_operations():
    """Test basic cache get/set/delete operations."""
    cache_clear()

    # Test set and get
    cache_set("test_key", "test_value", ttl=60)
    assert cache_get("test_key") == "test_value"

    # Test delete
    cache_delete("test_key")
    assert cache_get("test_key") is None


def test_cache_ttl_jitter():
    """Test that TTL jitter is applied (±10%)."""
    cache_clear()

    # Set with TTL=100 seconds
    # Expected actual TTL: 90-110 seconds
    cache_set("jitter_test", "value", ttl=100)

    # We can't directly measure TTL, but we can verify the value exists
    assert cache_get("jitter_test") == "value"

    # Note: Full jitter testing would require inspecting internal cache state
    # or using a real Redis instance with TTL inspection


def test_cache_expiration():
    """Test that cached values expire after TTL."""
    cache_clear()

    # Set with very short TTL (1 second)
    cache_set("expire_test", "value", ttl=1)

    # Should exist immediately
    assert cache_get("expire_test") == "value"

    # Wait for expiration
    time.sleep(1.5)

    # Should be expired
    assert cache_get("expire_test") is None


def test_cache_invalidate_prefix():
    """Test prefix-based cache invalidation."""
    cache_clear()

    # Set multiple keys with different prefixes
    cache_set("user:1", "alice", ttl=300)
    cache_set("user:2", "bob", ttl=300)
    cache_set("user:3", "charlie", ttl=300)
    cache_set("product:1", "laptop", ttl=300)
    cache_set("product:2", "phone", ttl=300)
    cache_set("order:1", "order_data", ttl=300)

    # Verify all keys exist
    assert cache_get("user:1") == "alice"
    assert cache_get("product:1") == "laptop"
    assert cache_get("order:1") == "order_data"

    # Invalidate user prefix
    cache_invalidate("user")

    # User keys should be gone
    assert cache_get("user:1") is None
    assert cache_get("user:2") is None
    assert cache_get("user:3") is None

    # Other keys should still exist
    assert cache_get("product:1") == "laptop"
    assert cache_get("product:2") == "phone"
    assert cache_get("order:1") == "order_data"

    # Invalidate product prefix
    cache_invalidate("product")

    # Product keys should be gone
    assert cache_get("product:1") is None
    assert cache_get("product:2") is None

    # Order should still exist
    assert cache_get("order:1") == "order_data"


def test_cache_invalidate_all():
    """Test invalidating all cache entries."""
    cache_clear()

    # Set multiple keys
    cache_set("key1", "value1", ttl=300)
    cache_set("key2", "value2", ttl=300)
    cache_set("key3", "value3", ttl=300)

    # Verify all exist
    assert cache_get("key1") == "value1"
    assert cache_get("key2") == "value2"
    assert cache_get("key3") == "value3"

    # Invalidate all (no prefix)
    cache_invalidate(None)

    # All should be gone
    assert cache_get("key1") is None
    assert cache_get("key2") is None
    assert cache_get("key3") is None


def test_cache_with_complex_data():
    """Test caching complex data structures."""
    cache_clear()

    # Test with dict
    data = {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "price": 180.5,
        "holdings": ["MSFT", "GOOGL", "AMZN"]
    }

    cache_set("stock:AAPL", data, ttl=60)
    retrieved = cache_get("stock:AAPL")

    assert retrieved == data
    assert retrieved["name"] == "Apple Inc."
    assert retrieved["holdings"] == ["MSFT", "GOOGL", "AMZN"]


def test_cache_overwrite():
    """Test that setting same key overwrites previous value."""
    cache_clear()

    cache_set("overwrite_test", "old_value", ttl=60)
    assert cache_get("overwrite_test") == "old_value"

    cache_set("overwrite_test", "new_value", ttl=60)
    assert cache_get("overwrite_test") == "new_value"
