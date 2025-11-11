"""Learned quantisation policy stubs."""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn


class QuantisationHead(nn.Module):
    """Outputs metadata describing the quantisation policy to apply."""

    def __init__(self, policy_cfg: Dict) -> None:
        super().__init__()
        self.default_bits = policy_cfg.get("default_bits", 8)
        self.allow_learned = policy_cfg.get("allow_learned", False)
        self.fc = nn.Linear(4, 4)

    def forward(self, context: Dict) -> Dict[str, float]:
        lod = float(context.get("lod", 1))
        stats = self.fc(torch.tensor([[lod, lod**2, 1.0, 0.5]])).squeeze(0)
        bits = self.default_bits - float(stats.mean().item()) * 0.1 if self.allow_learned else self.default_bits
        return {"quant_bits": max(2.0, bits)}


__all__ = ["QuantisationHead"]
