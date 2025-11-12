"""LayerNorm using procedurally generated affine parameters."""
from __future__ import annotations

import torch


def procedural_layernorm(hidden: torch.Tensor, weight: torch.Tensor, eps: float = 1e-5) -> torch.Tensor:
    mean = hidden.mean(dim=-1, keepdim=True)
    var = hidden.var(dim=-1, unbiased=False, keepdim=True)
    normed = (hidden - mean) / torch.sqrt(var + eps)
    return normed * weight


__all__ = ["procedural_layernorm"]
