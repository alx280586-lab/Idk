"""Precision control policies for procedural parameters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch


@dataclass
class PrecisionPolicy:
    """Precision controller selecting bitwidth per block type."""

    default_bits: int = 8
    overrides: Dict[str, int] | None = None

    def bits_for(self, block_type: str) -> int:
        if self.overrides and block_type in self.overrides:
            return self.overrides[block_type]
        return self.default_bits

    def quantize(self, tensor: torch.Tensor, block_type: str, training: bool = False) -> torch.Tensor:
        """Apply fake quantisation with a straight-through estimator when training."""

        bits = self.bits_for(block_type)
        levels = max(1, 2 ** (bits - 1) - 1)
        max_val = tensor.detach().abs().max()
        if max_val == 0:
            return tensor
        scale = max_val / levels
        quantized = torch.round(tensor / scale) * scale
        if training:
            return tensor + (quantized - tensor).detach()
        return quantized


__all__ = ["PrecisionPolicy"]
