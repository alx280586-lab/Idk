"""Rule-driven reasoning engine to emulate organic thinking."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol

from .memory import KnowledgeBase, MemoryTrace


class EvaluationStrategy(Protocol):
    """Callable strategy for evaluating generated artifacts."""

    def __call__(self, artifact: str) -> float:
        ...


@dataclass
class Thought:
    """Represents an internal reasoning step."""

    objective: str
    considerations: List[str]
    conclusion: str
    confidence: float


class Reasoner:
    """Hybrid planner that combines heuristics with rule scripts."""

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        evaluators: Dict[str, EvaluationStrategy],
    ) -> None:
        self.knowledge_base = knowledge_base
        self.evaluators = evaluators

    def brainstorm(self, goal: str, context: Dict[str, str]) -> Thought:
        """Produce a thought object based on heuristics."""
        considerations: List[str] = []
        for keyword in context.get("keywords", "").split():
            matches = self.knowledge_base.search([keyword])
            considerations.extend(
                f"Found {len(matches)} resources about '{keyword}'"
                if matches
                else f"No curated data about '{keyword}'"
            )
        conclusion = f"Plan crafted for goal: {goal}"
        confidence = min(0.95, 0.5 + 0.1 * len(considerations))
        return Thought(goal, considerations or ["Fallback heuristic"], conclusion, confidence)

    def evaluate(self, artifact: str) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for name, evaluator in self.evaluators.items():
            try:
                scores[name] = evaluator(artifact)
            except Exception:  # noqa: BLE001 - evaluation robustness over strictness
                scores[name] = 0.0
        return scores

    def refine(self, trace: MemoryTrace) -> MemoryTrace:
        """Adjust a trace's score based on evaluator feedback."""
        evaluations = self.evaluate(trace.response)
        aggregate = sum(evaluations.values()) / max(len(evaluations), 1)
        refined_score = 0.7 * trace.score + 0.3 * aggregate
        return MemoryTrace(trace.context, trace.response, refined_score, trace.tags)
