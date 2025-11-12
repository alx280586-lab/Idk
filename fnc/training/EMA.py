"""Exponential moving average utilities."""
from __future__ import annotations

from typing import Iterable

import torch


class EMA:
    """Maintain an exponential moving average of model parameters."""

    def __init__(self, parameters: Iterable[torch.nn.Parameter], decay: float) -> None:
        self.decay = decay
        self.shadow = [p.detach().clone() for p in parameters]
        self.params = list(parameters)

    @torch.no_grad()
    def update(self) -> None:
        for shadow, param in zip(self.shadow, self.params):
            shadow.mul_(self.decay).add_(param, alpha=1 - self.decay)


__all__ = ["EMA"]
