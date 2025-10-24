"""Evaluation harness for drafts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from .planner import PlanOutline
from .retrieval import RetrievedEvidence
from .coherence import CoherenceReport
from .critics import CriticFinding


@dataclass
class EvaluationReport:
    scores: Dict[str, float] = field(default_factory=dict)
    checklist: List[str] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "EvaluationReport":
        return cls()

    def to_dict(self) -> Dict[str, object]:
        return {"scores": self.scores, "checklist": self.checklist}


class EvaluationHarness:
    """Computes fluency, coherence, truth, and helpfulness scores."""

    def evaluate(
        self,
        draft: str,
        plan: PlanOutline,
        evidence: Sequence[RetrievedEvidence],
        coherence: CoherenceReport,
        critics: Sequence[CriticFinding],
    ) -> EvaluationReport:
        scores: Dict[str, float] = {}
        scores["fluency"] = self._fluency(draft)
        scores["coherence"] = coherence.score
        scores["fact"] = self._fact_score(evidence)
        scores["helpfulness"] = self._helpfulness(plan, draft)
        scores["policy_risk"] = self._policy_risk(critics)
        scores["contradiction"] = self._contradiction_penalty(critics)
        checklist = self._checklist(plan, draft)
        return EvaluationReport(scores=scores, checklist=checklist)

    def _fluency(self, draft: str) -> float:
        tokens = draft.split()
        if not tokens:
            return 0.0
        avg = sum(len(token) for token in tokens) / len(tokens)
        variance = sum((len(token) - avg) ** 2 for token in tokens) / len(tokens)
        rhythm = min(1.0, max(0.0, 1.0 - variance / 16))
        return rhythm

    def _fact_score(self, evidence: Sequence[RetrievedEvidence]) -> float:
        if not evidence:
            return 0.2
        total = sum(item.strength for item in evidence)
        return max(0.2, min(1.0, total / (len(evidence) * 2)))

    def _helpfulness(self, plan: PlanOutline, draft: str) -> float:
        coverage = 0
        for step in plan.steps:
            if step.focus.lower() in draft.lower():
                coverage += 1
        if not plan.steps:
            return 0.4
        return coverage / len(plan.steps)

    def _policy_risk(self, critics: Sequence[CriticFinding]) -> float:
        risks = [finding for finding in critics if finding.kind == "safety"]
        if not risks:
            return 0.0
        return min(1.0, 0.2 * len(risks))

    def _contradiction_penalty(self, critics: Sequence[CriticFinding]) -> float:
        contradictions = [finding for finding in critics if finding.kind == "logic" and finding.severity > 0.5]
        if not contradictions:
            return 0.0
        return min(1.0, 0.3 * len(contradictions))

    def _checklist(self, plan: PlanOutline, draft: str) -> List[str]:
        checklist: List[str] = []
        if "example" not in draft.lower():
            checklist.append("Add Example")
        if any(step.operator.name == "Compare" for step in plan.steps) and "trade" not in draft.lower():
            checklist.append("Call out trade-offs")
        return checklist
