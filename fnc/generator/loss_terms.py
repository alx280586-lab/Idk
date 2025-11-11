"""Auxiliary loss terms encouraging structure in generated weights."""
from __future__ import annotations

from typing import Dict

import torch


def coherence_loss(weights: torch.Tensor) -> torch.Tensor:
    """Penalise high variance to encourage smoothness."""
    return weights.std()


def reuse_loss(weights: torch.Tensor) -> torch.Tensor:
    """Encourage weight reuse by shrinking towards the mean."""
    return (weights - weights.mean()).abs().mean()


def entropy_control(weights: torch.Tensor) -> torch.Tensor:
    """Discourage collapse to a constant tensor."""
    return -torch.distributions.Normal(weights.mean(), weights.std() + 1e-6).entropy().mean()


def quant_stability(weights: torch.Tensor) -> torch.Tensor:
    """Placeholder quantisation stability measure."""
    return torch.var(weights)


def aggregate_losses(tensors: Dict[str, torch.Tensor]) -> torch.Tensor:
    """Combine multiple auxiliary losses into a scalar."""
    return sum(tensors.values())


__all__ = [
    "coherence_loss",
    "reuse_loss",
    "entropy_control",
    "quant_stability",
    "aggregate_losses",
]
