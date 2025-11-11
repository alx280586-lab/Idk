"""Optimizer factory for training the generator."""
from __future__ import annotations

from typing import Iterable

import torch


def build_optimizer(parameters: Iterable[torch.nn.Parameter], cfg) -> torch.optim.Optimizer:
    """Construct an AdamW optimizer with config defaults."""
    return torch.optim.AdamW(parameters, lr=cfg.training.lr, weight_decay=cfg.training.weight_decay)


__all__ = ["build_optimizer"]
