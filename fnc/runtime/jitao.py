"""Just-in-time assembly and optimisation helpers."""
from __future__ import annotations

from typing import Dict

from fnc.fnc_core.profiling import time_block


def assemble_block(block_key: str, generator_stats: Dict[str, float], sink: Dict[str, float]) -> None:
    """Record the time spent assembling a block."""
    with time_block(f"assemble_{block_key}", sink):
        generator_stats.setdefault(block_key, 0.0)
        generator_stats[block_key] += 1.0


__all__ = ["assemble_block"]
