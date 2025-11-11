"""Spectral field decoders turning latent codes into tensors."""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn

from fnc.generator.fractal_primitives import fractional_brownian_motion


class SpectralFieldDecoder(nn.Module):
    """Simple MLP with Fourier-style activations."""

    def __init__(self, cfg) -> None:
        super().__init__()
        self.output_dim = cfg.latent_dim
        self.layers = nn.Sequential(
            nn.Linear(cfg.latent_dim, cfg.latent_dim),
            nn.SiLU(),
            nn.Linear(cfg.latent_dim, cfg.latent_dim),
        )

    def forward(self, latent: torch.Tensor, context: Dict) -> torch.Tensor:
        enriched = latent + fractional_brownian_motion(latent)
        return self.layers(enriched)


__all__ = ["SpectralFieldDecoder"]
