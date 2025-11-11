"""Routing heuristics for procedural block prefetching."""
from __future__ import annotations

from typing import Dict, Iterable


def simple_routing_plan(seq_len: int, n_layers: int) -> Iterable[Dict[str, int]]:
    """Yield placeholder routing metadata per layer."""
    for layer in range(n_layers):
        yield {"layer": layer, "future_tokens": max(0, seq_len - layer)}


__all__ = ["simple_routing_plan"]
