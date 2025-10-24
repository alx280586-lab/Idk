"""Critic passes for orchestrated drafts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .retrieval import RetrievedEvidence
from .planner import PlanOutline


@dataclass
class CriticFinding:
    kind: str
    message: str
    severity: float
    target: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "kind": self.kind,
            "message": self.message,
            "severity": self.severity,
            "target": self.target,
            "suggestion": self.suggestion,
        }


class Critic:
    name = "critic"

    def review(
        self,
        draft: str,
        evidence: Iterable[RetrievedEvidence],
        plan: PlanOutline,
    ) -> List[CriticFinding]:
        raise NotImplementedError


class LogicCritic(Critic):
    name = "logic"

    def review(self, draft: str, evidence: Iterable[RetrievedEvidence], plan: PlanOutline) -> List[CriticFinding]:
        findings: List[CriticFinding] = []
        for step in plan.steps:
            if step.focus.lower() not in draft.lower():
                findings.append(
                    CriticFinding(
                        kind="logic",
                        message=f"Missing explicit reference to {step.focus}.",
                        severity=0.7,
                        suggestion=f"Add a paragraph linking to {step.focus} insight.",
                    )
                )
        return findings


class StyleCritic(Critic):
    name = "style"

    def review(self, draft: str, evidence: Iterable[RetrievedEvidence], plan: PlanOutline) -> List[CriticFinding]:
        findings: List[CriticFinding] = []
        sentences = draft.split(".")
        repeats = set()
        seen = set()
        for sentence in sentences:
            stripped = sentence.strip()
            if not stripped:
                continue
            lowered = stripped.lower()
            if lowered in seen:
                repeats.add(stripped)
            seen.add(lowered)
        for repeat in repeats:
            findings.append(
                CriticFinding(
                    kind="style",
                    message="Sentence repetition detected.",
                    severity=0.3,
                    target=repeat,
                    suggestion=f"Rephrase: {repeat.capitalize()} while adding nuance.",
                )
            )
        return findings


class SafetyCritic(Critic):
    name = "safety"

    def review(self, draft: str, evidence: Iterable[RetrievedEvidence], plan: PlanOutline) -> List[CriticFinding]:
        sensitive_terms = {"exploit", "malware", "cheat"}
        findings: List[CriticFinding] = []
        for term in sensitive_terms:
            if term in draft.lower():
                findings.append(
                    CriticFinding(
                        kind="safety",
                        message=f"Sensitive topic '{term}' detected; recommend hedging.",
                        severity=0.6,
                        suggestion="Reframe with ethical guidance.",
                    )
                )
        return findings


class CriticSuite:
    """Runs critic modules sequentially."""

    def __init__(self) -> None:
        self._critics: List[Critic] = [LogicCritic(), StyleCritic(), SafetyCritic()]

    def review(
        self,
        draft: str,
        evidence: Iterable[RetrievedEvidence],
        plan: PlanOutline,
    ) -> List[CriticFinding]:
        findings: List[CriticFinding] = []
        for critic in self._critics:
            findings.extend(critic.review(draft, evidence, plan))
        return findings
