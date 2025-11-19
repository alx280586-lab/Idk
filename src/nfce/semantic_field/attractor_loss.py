"""Loss functions encouraging attractor states in the semantic field."""
from __future__ import annotations

import torch
import torch.nn.functional as F
from .field import FieldState


def attractor_loss(state: FieldState, target: torch.Tensor) -> torch.Tensor:
    """Mean squared error between current grid and target attractor."""
    return F.mse_loss(state.grid, target)


def sparsity_loss(grid: torch.Tensor, l1_weight: float = 1e-4) -> torch.Tensor:
    """Encourage sparse activation among patch networks."""
    return l1_weight * grid.abs().mean()


__all__ = ["attractor_loss", "sparsity_loss"]
