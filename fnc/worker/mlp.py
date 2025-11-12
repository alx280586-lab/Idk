"""MLP block using procedural weights."""
from __future__ import annotations

import torch
import torch.nn.functional as F


def procedural_mlp_forward(hidden: torch.Tensor, w1: torch.Tensor, w2: torch.Tensor) -> torch.Tensor:
    """Simple two-layer feedforward network."""
    return F.gelu(hidden @ w1) @ w2


__all__ = ["procedural_mlp_forward"]
