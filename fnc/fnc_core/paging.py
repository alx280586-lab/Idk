"""Paging helpers for moving procedural tensors between devices."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch


@dataclass
class PagingDecision:
    block_key: str
    target_device: torch.device
    reason: str


def plan_paging(cache_info: Dict[str, float], budget_bytes: int) -> PagingDecision:
    """Return a placeholder paging decision based on cache stats."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    reason = "budget_ok" if cache_info.get("hit_rate", 0.0) > 0.5 else "low_hit_rate"
    return PagingDecision(block_key="*", target_device=device, reason=reason)


__all__ = ["PagingDecision", "plan_paging"]
