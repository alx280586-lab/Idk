"""Training checkpoint utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import torch


def save_training_state(path: Path, state: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(state, path)


def load_training_state(path: Path) -> Dict:
    return torch.load(path, map_location="cpu")


__all__ = ["save_training_state", "load_training_state"]
