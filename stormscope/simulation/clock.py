"""Simulation clock controlling real-time progression."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class SimulationClock:
    """Maintain simulation time with support for pausing and skipping."""

    time_seconds: float = 0.0
    running: bool = True
    subscribers: List[Callable[[float], None]] = field(default_factory=list)

    def advance(self, dt: float) -> None:
        if not self.running:
            return
        self.time_seconds += dt
        for callback in list(self.subscribers):
            callback(self.time_seconds)

    def toggle_running(self) -> None:
        self.running = not self.running

    def skip_ahead(self, delta: float) -> None:
        self.time_seconds += delta
        for callback in list(self.subscribers):
            callback(self.time_seconds)

    def subscribe(self, callback: Callable[[float], None]) -> None:
        self.subscribers.append(callback)
