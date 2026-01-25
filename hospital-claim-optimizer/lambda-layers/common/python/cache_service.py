"""
Caching service for Lambda functions to improve performance.
Implements in-memory caching with TTL support.
"""
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import hashlib
import json


class CacheService:
    """In-memory cache with TTL support for Lambda functions."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL."""
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }
    
    def delete(self, key: str):
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]


# Global cache instance for Lambda container reuse
_global_cache = CacheService()


def get_cache() -> CacheService:
    """Get global cache instance."""
    return _global_cache


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl_seconds: int = 300):
    """Decorator to cache function results."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator
