"""Shared utility helpers for the FNC project."""
from __future__ import annotations

import random
from typing import Iterable, Sequence

try:  # pragma: no cover - optional dependency in tests
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency in tests
    np = None  # type: ignore[assignment]
import torch


def init_seed(seed: int) -> None:
    """Initialise Python, NumPy, and Torch RNGs with the same seed."""
    random.seed(seed)
    if np is not None:
        np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():  # pragma: no cover - depends on hardware
        torch.cuda.manual_seed_all(seed)


def chunk_sequence(seq: Sequence[int], chunk_size: int) -> Iterable[Sequence[int]]:
    """Yield fixed-size chunks from *seq* without copying."""
    for idx in range(0, len(seq), chunk_size):
        yield seq[idx : idx + chunk_size]


__all__ = ["init_seed", "chunk_sequence"]
