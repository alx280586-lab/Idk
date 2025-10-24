"""Deliberative planner implementing HTN-style operators."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from .thought_graph import ThoughtNode
from .coherence import CoherenceReport
from .style import StyleSelection
from .retrieval import RetrievedEvidence
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .critics import CriticFinding


@dataclass
class PlanOperator:
    """Describes a reasoning operator used in structured planning."""

    name: str
    description: str
    inputs: List[str]
    guarantees: List[str]


@dataclass
class PlanStep:
    """Concrete step produced by the planner."""

    operator: PlanOperator
    focus: str
    evidence_requirements: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "operator": self.operator.name,
            "focus": self.focus,
            "requirements": list(self.evidence_requirements),
        }


@dataclass
class PlanOutline:
    """Structured representation of a plan."""

    goal: str
    steps: List[PlanStep] = field(default_factory=list)

    def to_nodes(self) -> Iterable[ThoughtNode]:
        for index, step in enumerate(self.steps):
            yield ThoughtNode(
                identifier=f"step-{index}",
                label=step.operator.name,
                content=f"Focus: {step.focus}",
                metadata={"requirements": step.evidence_requirements},
            )

    def to_dict(self) -> Dict[str, object]:
        return {
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
        }

    @property
    def harvest_queries(self) -> List[str]:
        queries: List[str] = []
        for step in self.steps:
            queries.extend(step.evidence_requirements)
        return queries


class DeliberativePlanner:
    """Hierarchical planner that maps intents to structured operators."""

    def __init__(self) -> None:
        self._operators = self._build_operators()

    def normalise_intent(self, prompt: str) -> str:
        return prompt.strip().capitalize()

    def build_plan(self, intent: str, focus_terms: Sequence[str]) -> PlanOutline:
        focus_list = list(focus_terms) or [intent]
        steps: List[PlanStep] = []
        for term in focus_list[:5]:
            operator = self._select_operator(intent, term)
            requirements = self._requirements_for(operator, term)
            steps.append(PlanStep(operator=operator, focus=term, evidence_requirements=requirements))
        return PlanOutline(goal=intent, steps=steps)

    def compose_draft(
        self,
        plan: PlanOutline,
        evidence: Sequence[RetrievedEvidence],
        style: StyleSelection,
    ) -> str:
        paragraphs: List[str] = []
        by_requirement: Dict[str, List[RetrievedEvidence]] = {}
        for item in evidence:
            for tag in item.tags:
                by_requirement.setdefault(tag, []).append(item)
        for step in plan.steps:
            sentences: List[str] = []
            opener = style.opening(step.operator.name)
            sentences.append(f"{opener} {step.focus}.")
            for requirement in step.evidence_requirements:
                supporting = by_requirement.get(requirement, [])
                if supporting:
                    best = max(supporting, key=lambda ev: ev.strength)
                    sentences.append(best.summary)
            if step.operator.name in {"Design", "Refactor"}:
                sentences.append(style.action_prompt(step.focus))
            paragraphs.append(" ".join(sentences))
        tail = style.closing(plan.goal, evidence)
        if tail:
            paragraphs.append(tail)
        return "\n\n".join(paragraphs)

    def apply_repairs(
        self,
        draft: str,
        findings: Sequence["CriticFinding"],
        coherence: Optional[CoherenceReport],
    ) -> str:
        patched = draft
        for finding in findings:
            if finding.kind == "logic" and finding.suggestion:
                patched += f"\n\nClarification: {finding.suggestion}."
            elif finding.kind == "style" and finding.suggestion:
                patched = patched.replace(finding.target or "", finding.suggestion)
        if coherence and coherence.score < 0.5:
            patched += "\n\nReordered for continuity after coherence remediation."
        return patched

    # Internal helpers -------------------------------------------------
    def _build_operators(self) -> List[PlanOperator]:
        return [
            PlanOperator("Explain", "Clarify core concept", ["question"], ["definition"]),
            PlanOperator("Compare", "Contrast alternatives", ["option"], ["tradeoff"]),
            PlanOperator("Judge", "Evaluate suitability", ["criterion"], ["verdict"]),
            PlanOperator("Design", "Synthesize solution", ["component"], ["blueprint"]),
            PlanOperator("Refactor", "Improve code", ["code"], ["improvement"]),
            PlanOperator("Summarize", "Condense knowledge", ["topic"], ["summary"]),
            PlanOperator("Forecast", "Project future", ["trend"], ["projection"]),
        ]

    def _select_operator(self, intent: str, term: str) -> PlanOperator:
        lowered = intent.lower()
        if any(keyword in lowered for keyword in ("compare", "vs", "difference")):
            return self._operator_named("Compare")
        if any(keyword in lowered for keyword in ("design", "build", "create")):
            return self._operator_named("Design")
        if any(keyword in lowered for keyword in ("refactor", "improve", "clean")):
            return self._operator_named("Refactor")
        if any(keyword in lowered for keyword in ("forecast", "predict")):
            return self._operator_named("Forecast")
        if "why" in lowered or "should" in lowered:
            return self._operator_named("Judge")
        if "summary" in lowered or "tl;dr" in lowered:
            return self._operator_named("Summarize")
        if term.lower() in {"code", "lua", "luau"}:
            return self._operator_named("Design")
        return self._operator_named("Explain")

    def _requirements_for(self, operator: PlanOperator, term: str) -> List[str]:
        base = [f"{operator.name}:{req}:{term}" for req in operator.inputs]
        extras = [f"evidence:{operator.name}:{term}"]
        return base + extras

    def _operator_named(self, name: str) -> PlanOperator:
        for operator in self._operators:
            if operator.name == name:
                return operator
        raise KeyError(name)
