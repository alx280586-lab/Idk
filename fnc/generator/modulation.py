"""Modulation layers for conditioning on context."""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn


class ContextModulator(nn.Module):
    """FiLM-style modulation combining latent codes with coordinates."""

    def __init__(self, coord_dim: int, latent_dim: int) -> None:
        super().__init__()
        self.coord_proj = nn.Linear(coord_dim, latent_dim)
        self.scale = nn.Linear(latent_dim, latent_dim)
        self.shift = nn.Linear(latent_dim, latent_dim)

    def forward(self, latent: torch.Tensor, coords: torch.Tensor, context: Dict) -> torch.Tensor:
        coord_embed = self.coord_proj(coords.float())
        scale = torch.tanh(self.scale(coord_embed)) + 1.0
        shift = self.shift(coord_embed)
        return latent * scale + shift


__all__ = ["ContextModulator"]
