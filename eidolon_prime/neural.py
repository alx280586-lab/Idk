"""Lightweight neural and specialist collectives powering organic speech."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, Iterable, List, Optional, Sequence

from .comprehension import MessageUnderstanding
from .synthetic import SyntheticThoughtPlan
from .orchestrator import OrchestratorResult


@dataclass
class NeuralActivation:
    """Snapshot of the ultra neural network's interpretation of a message."""

    parameter_count: int
    focus_vector: List[float]
    attention_terms: List[str]
    summary: str


@dataclass
class SpecialistInsight:
    """Represents the contribution from a narrow specialist module."""

    name: str
    focus: str
    contribution: str
    confidence: float


@dataclass
class CollectiveReport:
    """Consensus reached by the narrow specialist collective."""

    insights: List[SpecialistInsight]
    consensus: str
    confidence: float
    adjustments: Dict[str, float]


class UltraNeuralNetwork:
    """Deterministic neural mesh that steers reasoning without huge weights."""

    def __init__(self, parameter_count: int, layers: Sequence[str]) -> None:
        self.parameter_count = int(parameter_count)
        self._layers = list(layers)

    def activate(
        self,
        message: str,
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
        orchestration: Optional[OrchestratorResult],
    ) -> NeuralActivation:
        tokens = [token for token in message.lower().split() if token]
        vector: List[float] = []
        denom = sqrt(len(tokens) or 1)
        for index, layer in enumerate(self._layers):
            weight = 1.0 + (index / max(1, len(self._layers) - 1))
            vector.append(weight * len(tokens) / denom)
        focus_terms: List[str] = []
        if understanding.focus_terms:
            focus_terms.extend(understanding.focus_terms[:6])
        if plan and plan.focus_terms:
            for term in plan.focus_terms:
                if term not in focus_terms:
                    focus_terms.append(term)
        if orchestration:
            intent_hint = getattr(orchestration.blackboard, "intent", "")
            if intent_hint:
                for term in intent_hint.split():
                    lowered = term.lower()
                    if lowered not in focus_terms:
                        focus_terms.append(lowered)
            draft_preview = orchestration.final_text.split()
            for term in draft_preview[:6]:
                lowered = term.lower().strip(".,:;!")
                if lowered and lowered not in focus_terms:
                    focus_terms.append(lowered)
        if not focus_terms:
            focus_terms = tokens[:6]
        summary = (
            "Neural mesh mapped the utterance across "
            f"{len(self._layers)} layered feature groups while tracking {len(focus_terms)} focus terms."
        )
        return NeuralActivation(
            parameter_count=self.parameter_count,
            focus_vector=vector,
            attention_terms=focus_terms,
            summary=summary,
        )


class NarrowSpecialist:
    """Single-purpose reasoning helper that debates within the collective."""

    def __init__(self, name: str, keywords: Sequence[str], bias: float = 0.65) -> None:
        self.name = name
        self._keywords = [keyword.lower() for keyword in keywords]
        self._bias = bias

    def deliberate(
        self,
        message: str,
        activation: NeuralActivation,
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
    ) -> Optional[SpecialistInsight]:
        lowered = message.lower()
        coverage = 0
        for keyword in self._keywords:
            if keyword in lowered:
                coverage += 1
        if understanding.focus_terms:
            coverage += sum(1 for term in understanding.focus_terms if term in self._keywords)
        if plan and plan.focus_terms:
            coverage += sum(1 for term in plan.focus_terms if term in self._keywords)
        if coverage == 0:
            return None
        focus = ", ".join(self._keywords[:4])
        contribution = (
            f"{self.name.title()} module cross-checked focus on {focus} with {coverage} matches"
            " and will insist on contextual clarity."
        )
        confidence = min(0.95, self._bias + 0.05 * coverage)
        return SpecialistInsight(
            name=self.name,
            focus=focus,
            contribution=contribution,
            confidence=confidence,
        )


class NarrowCollective:
    """Coordinates narrow AI specialists so they can debate and align."""

    def __init__(self, specialists: Iterable[NarrowSpecialist]) -> None:
        self._specialists = list(specialists)

    def consensus(
        self,
        message: str,
        activation: NeuralActivation,
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
    ) -> Optional[CollectiveReport]:
        insights: List[SpecialistInsight] = []
        for specialist in self._specialists:
            insight = specialist.deliberate(message, activation, understanding, plan)
            if insight:
                insights.append(insight)
        if not insights:
            return None
        average_confidence = sum(item.confidence for item in insights) / len(insights)
        attention = ", ".join(dict.fromkeys(activation.attention_terms[:6]))
        consensus_text = (
            f"Collective aligned on attention to {attention}"
            f" with average confidence {average_confidence:.2f}."
        )
        adjustments = {
            "lexical_weight": min(1.0, 0.4 + 0.1 * len(activation.attention_terms)),
            "reasoning_depth": min(1.0, 0.5 + 0.05 * len(insights)),
        }
        return CollectiveReport(
            insights=insights,
            consensus=consensus_text,
            confidence=average_confidence,
            adjustments=adjustments,
        )

