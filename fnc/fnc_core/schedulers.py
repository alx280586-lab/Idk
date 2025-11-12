"""Schedulers for progressive levels of detail."""
from __future__ import annotations

from typing import Callable


def constant_scheduler(step: int, value: float, *_args, **_kwargs) -> float:
    """Return a constant value regardless of the step."""
    return value


def linear_warmup(step: int, warmup_steps: int, max_value: float) -> float:
    """Linearly scale up to *max_value* over *warmup_steps*."""
    if warmup_steps <= 0:
        return max_value
    return max_value * min(1.0, step / warmup_steps)


__all__ = ["constant_scheduler", "linear_warmup"]
