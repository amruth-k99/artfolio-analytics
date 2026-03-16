"""
Thread-safe LRU (Least Recently Used) cache with optional TTL.

Designed for caching dimension lookups during event ingestion.
Each cache instance tracks hit/miss/eviction stats for observability.

Usage:
    cache = LRUCache(max_size=1024, ttl_seconds=3600)
    cache.put("key", 42)
    cache.get("key")  # → 42 (cache hit)
    cache.stats()     # → {"hits": 1, "misses": 0, "evictions": 0, ...}
"""

import time
import threading
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """Single cache entry with value and creation timestamp."""
    value: object
    created_at: float = field(default_factory=time.monotonic)


class LRUCache:
    """
    Thread-safe LRU cache with optional per-entry TTL expiry.

    Args:
        max_size:     Maximum number of entries before eviction (default 1024).
        ttl_seconds:  Time-to-live per entry in seconds. None = no expiry.
        name:         Human-readable name for logging and stats.
    """

    def __init__(
        self,
        max_size: int = 1024,
        ttl_seconds: float | None = None,
        name: str = "unnamed",
    ):
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self.name = name

        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()

        # Stats counters
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    # ── Public API ──────────────────────────────────────────────

    def get(self, key: str) -> object | None:
        """
        Retrieve value by key. Returns None on miss or expired entry.
        Moves the accessed entry to the end (most recently used).
        """
        with self._lock:
            entry = self._store.get(key)

            if entry is None:
                self._misses += 1
                return None

            # Check TTL expiry
            if self._is_expired(entry):
                del self._store[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._store.move_to_end(key)
            self._hits += 1
            return entry.value

    def put(self, key: str, value: object) -> None:
        """
        Insert or update a cache entry. Evicts the least recently
        used entry if the cache is at capacity.
        """
        with self._lock:
            # Update existing entry
            if key in self._store:
                self._store[key] = CacheEntry(value=value)
                self._store.move_to_end(key)
                return

            # Evict LRU entry if at capacity
            if len(self._store) >= self._max_size:
                self._store.popitem(last=False)
                self._evictions += 1

            self._store[key] = CacheEntry(value=value)

    def invalidate(self, key: str) -> bool:
        """Remove a specific key. Returns True if the key existed."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all entries and reset stats."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def stats(self) -> dict:
        """Return a snapshot of cache metrics."""
        with self._lock:
            total = self._hits + self._misses
            return {
                "name": self.name,
                "size": len(self._store),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
            }

    # ── Internal ────────────────────────────────────────────────

    def _is_expired(self, entry: CacheEntry) -> bool:
        if self._ttl_seconds is None:
            return False
        return (time.monotonic() - entry.created_at) > self._ttl_seconds
