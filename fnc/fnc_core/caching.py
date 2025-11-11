"""Caching infrastructure for procedurally generated tensors."""
from __future__ import annotations

import collections
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import torch


class CacheInterface:
    """Abstract cache API used by parameter proxies."""

    def lookup(self, key) -> Optional[torch.Tensor]:  # pragma: no cover - interface
        raise NotImplementedError

    def insert(self, key, tensor: torch.Tensor, cost: float, pin: bool = False) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def evict_until(self, bytes_target: int) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def info(self) -> Dict[str, float]:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class CacheEntry:
    tensor: torch.Tensor
    cost: float
    pinned: bool = False


class SimpleCache(CacheInterface):
    """A naive LRU cache for prototypes and tests."""

    def __init__(self, max_entries: int = 128) -> None:
        self.max_entries = max_entries
        self._store: Dict = {}
        self._order = collections.OrderedDict()
        self.hits = 0
        self.misses = 0

    def lookup(self, key) -> Optional[torch.Tensor]:
        entry = self._store.get(key)
        if entry is not None:
            self.hits += 1
            self._order.move_to_end(key)
            return entry.tensor
        self.misses += 1
        return None

    def insert(self, key, tensor: torch.Tensor, cost: float, pin: bool = False) -> None:
        if key in self._store:
            self._order.move_to_end(key)
        self._store[key] = CacheEntry(tensor=tensor, cost=cost, pinned=pin)
        self._order[key] = None
        self._evict_if_needed()

    def evict_until(self, bytes_target: int) -> None:
        while len(self._store) > bytes_target and self._order:
            victim, _ = self._order.popitem(last=False)
            entry = self._store[victim]
            if entry.pinned:
                self._order[victim] = None
                continue
            del self._store[victim]

    def _evict_if_needed(self) -> None:
        while len(self._store) > self.max_entries:
            victim, _ = self._order.popitem(last=False)
            entry = self._store[victim]
            if entry.pinned:
                self._order[victim] = None
                continue
            del self._store[victim]

    def info(self) -> Dict[str, float]:
        total = self.hits + self.misses
        hit_rate = self.hits / total if total else 0.0
        return {"hits": float(self.hits), "misses": float(self.misses), "hit_rate": hit_rate}


__all__ = ["CacheInterface", "SimpleCache"]
