"""Implementation of the fractal generator network."""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn

from fnc.generator.modulation import ContextModulator
from fnc.generator.spectral_fields import SpectralFieldDecoder
from fnc.generator.quantizer import QuantisationHead


class FractalGenerator(nn.Module):
    """Compact neural network producing weight blocks from seeds and coords."""

    def __init__(self, cfg) -> None:
        super().__init__()
        self.coord_embed_dim = cfg.coord_embed_dim
        self.latent_dim = cfg.latent_dim
        self.num_lod = cfg.num_lod
        self.modulator = ContextModulator(cfg.coord_embed_dim, cfg.latent_dim)
        self.field_decoder = SpectralFieldDecoder(cfg)
        self.quant_head = QuantisationHead(cfg.quant_policy)
        self.seed_mlp = nn.Sequential(
            nn.Linear(1, cfg.latent_dim),
            nn.SiLU(),
            nn.Linear(cfg.latent_dim, cfg.latent_dim),
        )

    def forward(self, seed: torch.Tensor, coords: torch.Tensor, context: Dict) -> Dict[str, torch.Tensor]:
        """Generate a weight block conditioned on *seed*, *coords*, and *context*."""
        seed = seed.float().reshape(-1, 1)
        latent = self.seed_mlp(seed)
        if coords.dim() == 1:
            coords = coords.unsqueeze(0)
        modulated = self.modulator(latent, coords, context)
        weights = self.field_decoder(modulated, context)
        aux = {
            "lod_used": int(context.get("lod", self.num_lod)),
            "smoothness": float(weights.std().item()),
        }
        quant_ctx = self.quant_head(context)
        aux.update(quant_ctx)
        return {"weights": weights, "aux": aux}


__all__ = ["FractalGenerator"]
