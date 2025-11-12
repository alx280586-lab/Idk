"""Checkpoint utilities for the generator."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import torch


def save_generator_checkpoint(path: Path, state: Dict) -> None:
    """Persist generator state to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(state, path)


def load_generator_checkpoint(path: Path) -> Dict:
    """Load generator state from *path*."""
    return torch.load(path, map_location="cpu")


__all__ = ["save_generator_checkpoint", "load_generator_checkpoint"]
