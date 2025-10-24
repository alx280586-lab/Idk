"""Coherence scoring utilities using entity grids."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import re

_ENTITY_REGEX = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")


@dataclass
class CoherenceReport:
    """Stores coherence metrics."""

    score: float
    entity_grid: Dict[str, List[str]]

    def to_dict(self) -> Dict[str, object]:
        return {"score": self.score, "entity_grid": self.entity_grid}


class CoherenceScorer:
    """Minimal entity grid scorer."""

    def score(self, draft: str) -> CoherenceReport:
        sentences = [sentence.strip() for sentence in re.split(r"[.!?]", draft) if sentence.strip()]
        grid: Dict[str, List[str]] = {}
        for index, sentence in enumerate(sentences):
            tokens = _ENTITY_REGEX.findall(sentence)
            for token in tokens:
                roles = grid.setdefault(token.lower(), ["-"] * len(sentences))
                role = "S" if index == 0 else ("O" if index % 2 else "X")
                roles[index] = role
        score = self._grid_score(grid, len(sentences))
        return CoherenceReport(score=score, entity_grid=grid)

    def _grid_score(self, grid: Dict[str, List[str]], sentence_count: int) -> float:
        if sentence_count < 2 or not grid:
            return 0.5
        transitions = 0
        penalties = 0
        for roles in grid.values():
            for idx in range(1, sentence_count):
                prev = roles[idx - 1]
                curr = roles[idx]
                if prev in {"S", "O"} and curr in {"S", "O"}:
                    transitions += 1
                elif prev == "-" and curr == "-":
                    penalties += 1
        total = max(1, sentence_count - 1)
        base = transitions / total
        penalty = penalties / max(1, len(grid) * total)
        return max(0.0, min(1.0, base - penalty / 2))
