"""Profiling utilities for procedural generation latency."""
from __future__ import annotations

import contextlib
import time
from typing import Dict, Iterator


@contextlib.contextmanager
def time_block(name: str, sink: Dict[str, float]) -> Iterator[None]:
    """Measure execution time of a code block in seconds."""
    start = time.perf_counter()
    try:
        yield
    finally:
        sink[name] = sink.get(name, 0.0) + (time.perf_counter() - start)


__all__ = ["time_block"]
