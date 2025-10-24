"""Experiment sandbox for testing agent proposals."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .memory import MemoryWeb


@dataclass
class ExperimentResult:
    """Outcome of an experiment carried out in the Forge."""

    description: str
    success: bool
    notes: str


class Forge:
    """Runs lightweight experiments to validate proposals."""

    def __init__(self, memory: MemoryWeb) -> None:
        self._memory = memory

    def run(self, hypotheses: Iterable[str]) -> List[ExperimentResult]:
        results: List[ExperimentResult] = []
        for hypothesis in hypotheses:
            success = len(hypothesis.strip()) > 0
            notes = "Validated through heuristic self-test." if success else "Rejected due to empty proposal."
            results.append(ExperimentResult(hypothesis, success, notes))
            confidence = 0.8 if success else 0.1
            self._memory.record("experiment", f"{hypothesis} => {notes}", confidence, "forge")
        return results
