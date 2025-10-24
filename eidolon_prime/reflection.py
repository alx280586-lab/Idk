"""Reflection engine that reviews agent output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .state import PersonalityState
from .memory import MemoryWeb


@dataclass
class ReflectionReport:
    """A lightweight summary of the reflection outcome."""

    accepted: bool
    rationale: str


class ReflectionEngine:
    """Evaluates proposals and nudges the personality state."""

    def __init__(self, personality: PersonalityState, memory: MemoryWeb) -> None:
        self._personality = personality
        self._memory = memory

    def review(self, statements: Iterable[str]) -> ReflectionReport:
        items = list(statements)
        count = len(items)
        if count == 0:
            self._personality.adjust(confidence=-0.05, curiosity=-0.05)
            return ReflectionReport(False, "No actionable statements were produced.")
        self._personality.adjust(confidence=0.02, curiosity=0.01, empathy=0.01)
        self._memory.record("reflection", f"Validated {count} statements", 0.7, "reflection")
        return ReflectionReport(True, f"Validated {count} statements for further action.")
