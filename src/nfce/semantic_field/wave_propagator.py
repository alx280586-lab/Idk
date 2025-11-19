"""Wave propagation utilities for the semantic field."""
from __future__ import annotations

import torch
from .field import FieldState, SemanticField


def propagate(field: SemanticField, state: FieldState, steps: int = 1, delta_t: float = 0.1) -> FieldState:
    """Iteratively propagate the field state."""
    current = state
    for _ in range(steps):
        current = field(current, delta_t=delta_t)
    return current


def inject_stimulus(state: FieldState, position: int, amplitude: float = 1.0) -> FieldState:
    """Inject a localized stimulus into the field grid."""
    grid = state.grid.clone()
    grid[..., position] += amplitude
    return FieldState(grid=grid, time=state.time)


__all__ = ["propagate", "inject_stimulus"]
