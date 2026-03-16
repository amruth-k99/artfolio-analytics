"""
CacheManager — central registry for all named LRU caches.

Provides a single point of access for creating, retrieving,
and monitoring caches across the application.

Usage:
    from src.cache import cache_manager

    # At startup (e.g. in main.py lifespan):
    cache_manager.register("ip_location", max_size=2048, ttl_seconds=3600)

    # In service code:
    ip_cache = cache_manager.get_cache("ip_location")
    ip_cache.get("192.168.1.1")
"""

from src.cache.lru import LRUCache


class CacheManager:
    """
    Singleton-style registry that holds all named cache instances.

    Register caches at app startup, then retrieve them by name
    wherever needed. Keeps cache configuration in one place.
    """

    def __init__(self):
        self._caches: dict[str, LRUCache] = {}

    def register(
        self,
        name: str,
        max_size: int = 1024,
        ttl_seconds: float | None = None,
    ) -> LRUCache:
        """
        Create and register a named cache. Returns the new cache.

        Raises ValueError if a cache with the same name already exists
        (prevents silent overwrites in production).
        """
        if name in self._caches:
            raise ValueError(
                f"Cache '{name}' is already registered. "
                f"Use get_cache('{name}') to access it."
            )

        cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds, name=name)
        self._caches[name] = cache
        return cache

    def get_cache(self, name: str) -> LRUCache:
        """
        Retrieve a registered cache by name.
        Raises KeyError if the cache has not been registered.
        """
        if name not in self._caches:
            raise KeyError(
                f"Cache '{name}' not found. "
                f"Available caches: {list(self._caches.keys())}. "
                f"Did you call cache_manager.register('{name}', ...) at startup?"
            )
        return self._caches[name]

    def stats(self) -> dict[str, dict]:
        """Return stats for every registered cache, keyed by name."""
        return {name: cache.stats() for name, cache in self._caches.items()}

    def clear_all(self) -> None:
        """Clear all entries in every registered cache."""
        for cache in self._caches.values():
            cache.clear()

    @property
    def cache_names(self) -> list[str]:
        """List all registered cache names."""
        return list(self._caches.keys())
