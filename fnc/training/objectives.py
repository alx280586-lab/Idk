"""Training objectives and auxiliary regularisers."""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn.functional as F

from fnc.generator.loss_terms import (
    aggregate_losses,
    coherence_loss,
    entropy_control,
    quant_stability,
    reuse_loss,
)


def language_model_loss(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """Compute cross-entropy loss for language modelling."""
    vocab_size = logits.size(-1)
    return F.cross_entropy(logits.view(-1, vocab_size), targets.view(-1))


def auxiliary_losses(stats: Dict) -> torch.Tensor:
    """Aggregate placeholder auxiliary losses."""
    dummy = torch.randn(1, requires_grad=True)
    losses = {
        "coherence": coherence_loss(dummy),
        "reuse": reuse_loss(dummy),
        "entropy": entropy_control(dummy),
        "quant_stability": quant_stability(dummy),
    }
    return aggregate_losses(losses)


__all__ = ["language_model_loss", "auxiliary_losses"]
