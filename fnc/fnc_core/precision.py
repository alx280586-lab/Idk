"""Precision control policies for procedural parameters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch


@dataclass
class PrecisionPolicy:
    """Simple precision controller selecting bitwidth per block type."""

    default_bits: int = 8
    overrides: Dict[str, int] = None

    def bits_for(self, block_type: str) -> int:
        if self.overrides and block_type in self.overrides:
            return self.overrides[block_type]
        return self.default_bits

    def quantize(self, tensor: torch.Tensor, block_type: str) -> torch.Tensor:
        """Apply a naive fake quantisation for placeholder purposes."""
        bits = self.bits_for(block_type)
        scale = tensor.abs().max() / max(1, (2 ** (bits - 1) - 1))
        if scale == 0:
            return tensor
        q = torch.round(tensor / scale)
        return q * scale


__all__ = ["PrecisionPolicy"]
