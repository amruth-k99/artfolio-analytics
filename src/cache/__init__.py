"""
Cache package — exposes LRUCache, CacheManager, and the global singleton.

Import the global cache_manager wherever you need a cache:
    from src.cache import cache_manager
"""

from src.cache.lru import LRUCache
from src.cache.manager import CacheManager

# Global singleton — import this everywhere.
# Caches are registered once at app startup (main.py lifespan).
cache_manager = CacheManager()

__all__ = ["LRUCache", "CacheManager", "cache_manager"]
