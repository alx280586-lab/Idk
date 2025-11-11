"""Evaluation helpers for tracking perplexity and cache stats."""
from __future__ import annotations

import math
from typing import Dict


def perplexity_from_loss(loss: float) -> float:
    """Convert cross-entropy loss to perplexity."""
    return float(math.exp(loss))


def summarise_runtime_metrics(cache_info: Dict[str, float]) -> Dict[str, float]:
    """Normalise runtime metrics for logging."""
    return {
        "cache_hit_rate": cache_info.get("hit_rate", 0.0),
        "cache_hits": cache_info.get("hits", 0.0),
        "cache_misses": cache_info.get("misses", 0.0),
    }


__all__ = ["perplexity_from_loss", "summarise_runtime_metrics"]
