"""
Unit tests for the LRU cache module.

Run with:
    python -m pytest tests/test_cache.py -v
"""

import time
import threading
from src.cache.lru import LRUCache


# ── Basic operations ────────────────────────────────────────────


class TestLRUCacheBasicOps:
    """Test core get/put/invalidate/clear operations."""

    def test_put_and_get(self):
        cache = LRUCache(max_size=10, name="test")
        cache.put("a", 1)
        assert cache.get("a") == 1

    def test_get_miss_returns_none(self):
        cache = LRUCache(max_size=10, name="test")
        assert cache.get("nonexistent") is None

    def test_put_overwrites_existing(self):
        cache = LRUCache(max_size=10, name="test")
        cache.put("a", 1)
        cache.put("a", 2)
        assert cache.get("a") == 2

    def test_invalidate_existing_key(self):
        cache = LRUCache(max_size=10, name="test")
        cache.put("a", 1)
        assert cache.invalidate("a") is True
        assert cache.get("a") is None

    def test_invalidate_missing_key(self):
        cache = LRUCache(max_size=10, name="test")
        assert cache.invalidate("nope") is False

    def test_clear(self):
        cache = LRUCache(max_size=10, name="test")
        cache.put("a", 1)
        cache.put("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


# ── Eviction ────────────────────────────────────────────────────


class TestLRUCacheEviction:
    """Test LRU eviction behavior when cache reaches max_size."""

    def test_evicts_lru_entry(self):
        cache = LRUCache(max_size=2, name="test")
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # should evict "a"

        assert cache.get("a") is None  # evicted
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_access_refreshes_lru_order(self):
        cache = LRUCache(max_size=2, name="test")
        cache.put("a", 1)
        cache.put("b", 2)

        # Access "a" to make it recently used
        cache.get("a")

        cache.put("c", 3)  # should evict "b" (least recently used)

        assert cache.get("a") == 1
        assert cache.get("b") is None  # evicted
        assert cache.get("c") == 3

    def test_eviction_count_tracked(self):
        cache = LRUCache(max_size=2, name="test")
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # evicts "a"
        cache.put("d", 4)  # evicts "b"

        stats = cache.stats()
        assert stats["evictions"] == 2


# ── TTL ─────────────────────────────────────────────────────────


class TestLRUCacheTTL:
    """Test time-to-live expiry."""

    def test_expired_entry_returns_none(self):
        cache = LRUCache(max_size=10, ttl_seconds=0.1, name="test")
        cache.put("a", 1)

        time.sleep(0.15)

        assert cache.get("a") is None

    def test_fresh_entry_returned(self):
        cache = LRUCache(max_size=10, ttl_seconds=10, name="test")
        cache.put("a", 1)

        assert cache.get("a") == 1  # not expired yet

    def test_no_ttl_means_no_expiry(self):
        cache = LRUCache(max_size=10, ttl_seconds=None, name="test")
        cache.put("a", 1)

        # Even after a tiny sleep, still alive
        time.sleep(0.05)
        assert cache.get("a") == 1


# ── Stats ───────────────────────────────────────────────────────


class TestLRUCacheStats:
    """Test hit/miss/eviction counters and hit rate."""

    def test_stats_initial(self):
        cache = LRUCache(max_size=10, name="test_stats")
        stats = cache.stats()
        assert stats["name"] == "test_stats"
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["size"] == 0

    def test_stats_after_operations(self):
        cache = LRUCache(max_size=10, name="test")
        cache.put("a", 1)
        cache.get("a")     # hit
        cache.get("b")     # miss
        cache.get("a")     # hit

        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == round(2 / 3, 4)

    def test_clear_resets_stats(self):
        cache = LRUCache(max_size=10, name="test")
        cache.put("a", 1)
        cache.get("a")     # hit
        cache.clear()

        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


# ── Thread safety ───────────────────────────────────────────────


class TestLRUCacheThreadSafety:
    """Verify no crashes under concurrent access."""

    def test_concurrent_puts_no_crash(self):
        cache = LRUCache(max_size=100, name="threaded")
        errors = []

        def writer(start: int):
            try:
                for i in range(100):
                    cache.put(f"key-{start + i}", i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t * 100,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert cache.stats()["size"] <= 100  # respects max_size
