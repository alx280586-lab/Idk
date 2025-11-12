"""Coordinate encoding utilities for procedural weight generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import torch


@dataclass
class CoordinateSpec:
    block_type: str
    layer: int
    head: int
    row: int
    col: int


class CoordinateEncoder:
    """Encodes block specifications into continuous coordinates."""

    def __init__(self, embed_dim: int = 64) -> None:
        self.embed_dim = embed_dim

    def encode(self, spec: Tuple) -> torch.Tensor:
        """Encode a block spec into a coordinate tensor."""
        block_type, layer, head, row, col = spec
        base = torch.tensor([float(layer), float(head), float(row), float(col)], dtype=torch.float32)
        type_hash = float(abs(hash(block_type)) % 10_000)
        coords = torch.cat([torch.tensor([type_hash]), base])
        if coords.numel() < self.embed_dim:
            padding = torch.zeros(self.embed_dim - coords.numel())
            coords = torch.cat([coords, padding])
        else:
            coords = coords[: self.embed_dim]
        return coords

    def batch(self, specs: Iterable[Tuple]) -> torch.Tensor:
        """Batch encode multiple specs."""
        return torch.stack([self.encode(spec) for spec in specs], dim=0)


__all__ = ["CoordinateEncoder", "CoordinateSpec"]
