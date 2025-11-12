"""Prefetch planning for upcoming procedural blocks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class PrefetchRequest:
    block_key: str
    lead_time: int


class PrefetchPlanner:
    """Naive planner that prefetches the next N blocks."""

    def __init__(self, window: int = 2) -> None:
        self.window = window

    def plan(self, upcoming: Iterable[str]) -> List[PrefetchRequest]:
        plan = []
        for lead_time, block in enumerate(upcoming):
            if lead_time >= self.window:
                break
            plan.append(PrefetchRequest(block_key=block, lead_time=lead_time))
        return plan


__all__ = ["PrefetchPlanner", "PrefetchRequest"]
