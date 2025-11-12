"""High-level cache policies built on top of CacheInterface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from fnc.fnc_core.caching import SimpleCache


@dataclass
class CachePolicy:
    """Wraps a cache implementation with a policy name."""

    name: str = "lru"
    cache: SimpleCache = SimpleCache()

    def info(self) -> Dict[str, float]:
        return self.cache.info()


__all__ = ["CachePolicy"]
