"""Local patch networks that gate semantic field updates."""
from __future__ import annotations

import torch
import torch.nn as nn


class PatchNetwork(nn.Module):
    """Tiny MLP operating on a patch of the field grid."""

    def __init__(self, input_size: int = 8, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden),
            nn.ReLU(),
            nn.Linear(hidden, input_size),
        )

    def forward(self, patch: torch.Tensor) -> torch.Tensor:
        return self.net(patch)


class PatchBank(nn.Module):
    """Collection of patch networks supporting sparse activation."""

    def __init__(self, patch_size: int = 8, num_patches: int = 16):
        super().__init__()
        self.patch_size = patch_size
        self.patches = nn.ModuleList([PatchNetwork(patch_size) for _ in range(num_patches)])

    def forward(self, grid: torch.Tensor) -> torch.Tensor:
        outputs = []
        for idx, patch_net in enumerate(self.patches):
            segment = grid[..., idx : idx + self.patch_size]
            outputs.append(patch_net(segment))
        return torch.stack(outputs, dim=1)


__all__ = ["PatchNetwork", "PatchBank"]
