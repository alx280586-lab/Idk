"""Projects raw text into initial wave packets."""
from __future__ import annotations

import torch
from .semantic_field.field import FieldState
from .tone_emotion_module import score_text


def project_text(text: str, grid_size: int = 128) -> FieldState:
    tone = score_text(text)
    grid = torch.zeros(1, 8, grid_size)
    magnitude = sum(tone.values())
    grid[..., 0] = magnitude
    return FieldState(grid=grid, time=0.0)


__all__ = ["project_text"]
