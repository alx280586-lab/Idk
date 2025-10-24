"""Personality state tracking."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PersonalityState:
    """Mutable representation of the system's personality vectors."""

    curiosity: float = 0.5
    confidence: float = 0.5
    empathy: float = 0.5
    integrity: float = 0.8

    def adjust(self, curiosity: float = 0.0, confidence: float = 0.0, empathy: float = 0.0, integrity: float = 0.0) -> None:
        """Adjust internal state by clamped deltas."""
        self.curiosity = _clamp(self.curiosity + curiosity)
        self.confidence = _clamp(self.confidence + confidence)
        self.empathy = _clamp(self.empathy + empathy)
        self.integrity = _clamp(self.integrity + integrity)

    def describe(self) -> str:
        return (
            f"Curiosity {self.curiosity:.2f}, "
            f"Confidence {self.confidence:.2f}, "
            f"Empathy {self.empathy:.2f}, "
            f"Integrity {self.integrity:.2f}"
        )


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))
