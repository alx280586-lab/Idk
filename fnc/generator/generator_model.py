"""Implementation of the fractal generator network."""
from __future__ import annotations

import math
from typing import Dict, Tuple

import torch
import torch.nn as nn

from fnc.generator.modulation import ContextModulator
from fnc.generator.spectral_fields import SpectralFieldDecoder
from fnc.generator.quantizer import QuantisationHead
from fnc.generator.fractal_primitives import fractional_brownian_motion


def _grid_features(shape: Tuple[int, ...], latent_dim: int, lod: int) -> torch.Tensor:
    """Build a spectral feature grid for the requested tensor ``shape``.

    The implementation enumerates every coordinate in the block, computes
    harmonic features for each level of detail, and packs the result into a
    dense matrix suitable for linear projection with the latent basis.
    """

    dims = len(shape)
    axes = [torch.linspace(-1.0, 1.0, steps=max(1, s)).tolist() for s in shape]
    from itertools import product

    coords: list[Tuple[float, ...]]
    if dims == 0:
        coords = [(0.0,)]
    else:
        coords = list(product(*axes))
    rows = []
    lod_levels = max(1, lod)
    for coord in coords:
        row = list(coord)
        for level in range(1, lod_levels + 1):
            freq = 2.0 ** (level - 1)
            for value in coord:
                angle = value * math.pi * freq
                row.append(math.sin(angle))
                row.append(math.cos(angle))
        rows.append(row)
    spectral = torch.tensor(rows)
    fbm = fractional_brownian_motion(spectral)
    enriched = spectral + fbm
    if enriched.shape[1] < latent_dim:
        padding = torch.zeros(enriched.shape[0], latent_dim - enriched.shape[1])
        enriched = torch.cat([enriched, padding], dim=1)
    else:
        enriched = enriched[:, :latent_dim]
    return enriched


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
        if seed.dim() == 0:
            seed = seed.view(1, 1)
        else:
            seed = seed.float().view(-1, 1)
        if coords.dim() == 1:
            coords = coords.unsqueeze(0)
        coords = coords.to(seed.device)
        latent = self.seed_mlp(seed.float())
        modulated = self.modulator(latent, coords, context)
        decoded = self.field_decoder(modulated, coords, context)
        lod = int(context.get("lod", self.num_lod))
        shape = tuple(int(x) for x in context.get("shape", (decoded.size(-1),)))
        if not shape:
            shape = (decoded.size(-1),)
        grid = _grid_features(shape, decoded.shape[-1], lod)
        weights = (decoded @ grid.transpose(0, 1)).reshape(decoded.shape[0], *shape)
        aux = {
            "lod_used": lod,
            "smoothness": float(weights.std().item()),
            "virtual_params": float(grid.size(0) * lod),
        }
        quant_ctx = self.quant_head(context)
        aux.update(quant_ctx)
        return {"weights": weights, "aux": aux}


__all__ = ["FractalGenerator"]
