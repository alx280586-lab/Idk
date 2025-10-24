"""Reasoning orchestrator with blackboard scheduling and multi-pass critics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import json
import time
from pathlib import Path

from .planner import DeliberativePlanner, PlanOutline
from .retrieval import RetrievalManager, RetrievedEvidence
from .knowledge_graph import KnowledgeGraph, WorldEvent
from .coherence import CoherenceScorer, CoherenceReport
from .style import StyleProfile, StyleSelection
from .evaluation import EvaluationHarness, EvaluationReport
from .critics import CriticSuite, CriticFinding
from .thought_graph import ThoughtGraph, ThoughtNode


@dataclass
class Blackboard:
    """Shared state used by orchestrated reasoning modules."""

    intent: str
    context_graph: Dict[str, Any] = field(default_factory=dict)
    argument_graph: Dict[str, Any] = field(default_factory=dict)
    drafts: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    evidence: List[RetrievedEvidence] = field(default_factory=list)
    timeline: List[WorldEvent] = field(default_factory=list)
    style: Optional[StyleSelection] = None
    coherence: Optional[CoherenceReport] = None
    evaluations: Optional[EvaluationReport] = None
    plan: Optional[PlanOutline] = None
    thought_graph: ThoughtGraph = field(default_factory=ThoughtGraph)
    trace: List[Dict[str, Any]] = field(default_factory=list)

    def post(self, label: str, payload: Dict[str, Any]) -> None:
        stamp = {"label": label, "payload": payload, "ts": time.time()}
        self.trace.append(stamp)

    def add_draft(self, draft: str) -> None:
        if draft:
            self.drafts.append(draft)
            self.post("draft", {"length": len(draft), "preview": draft[:200]})


@dataclass
class ModuleBudget:
    """Budgets tracked by the scheduler."""

    token_budget: int
    time_budget: float
    web_calls: int


class Scheduler:
    """Simple cooperative scheduler that enforces module budgets."""

    def __init__(self, budgets: ModuleBudget) -> None:
        self._budgets = budgets
        self._start = time.time()
        self._round = 0

    @property
    def round(self) -> int:
        return self._round

    def start_round(self, label: str, blackboard: Blackboard) -> None:
        self._round += 1
        blackboard.post("round", {"round": self._round, "label": label})

    def consume(self, *, tokens: int = 0, web: int = 0) -> None:
        self._budgets.token_budget = max(0, self._budgets.token_budget - tokens)
        self._budgets.web_calls = max(0, self._budgets.web_calls - web)

    def time_exceeded(self) -> bool:
        return (time.time() - self._start) > self._budgets.time_budget

    def has_budget(self) -> bool:
        return (
            self._budgets.token_budget > 0
            and self._budgets.web_calls >= 0
            and not self.time_exceeded()
        )


@dataclass
class OrchestratorResult:
    """Final artefacts emitted after orchestration."""

    final_text: str
    citations: List[str]
    confidence: float
    blackboard: Blackboard
    critics: List[CriticFinding]
    evaluation: EvaluationReport
    coherence: Optional[CoherenceReport]
    style: Optional[StyleSelection]
    trace_path: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "final_text": self.final_text,
                "citations": self.citations,
                "confidence": self.confidence,
                "trace": self.blackboard.trace,
                "scores": self.blackboard.scores,
                "evaluation": self.evaluation.to_dict(),
                "coherence": self.coherence.to_dict() if self.coherence else None,
                "style": self.style.to_dict() if self.style else None,
                "critics": [finding.to_dict() for finding in self.critics],
            },
            indent=2,
        )


class ReasoningOrchestrator:
    """Coordinates planner, retrieval, drafting, and critics into a traceable flow."""

    def __init__(
        self,
        planner: DeliberativePlanner,
        retrieval: RetrievalManager,
        knowledge_graph: KnowledgeGraph,
        coherence: CoherenceScorer,
        style: StyleProfile,
        evaluation: EvaluationHarness,
        critics: CriticSuite,
        *,
        default_trace_path: str = "trace.json",
    ) -> None:
        self._planner = planner
        self._retrieval = retrieval
        self._knowledge_graph = knowledge_graph
        self._coherence = coherence
        self._style = style
        self._evaluation = evaluation
        self._critics = critics
        self._trace_path = default_trace_path

    def execute(
        self,
        prompt: str,
        *,
        context_terms: Sequence[str],
        memory_topics: Sequence[str],
        understanding_summary: Optional[str] = None,
        prior_plan: Optional[PlanOutline] = None,
    ) -> OrchestratorResult:
        blackboard = Blackboard(intent=prompt)
        scheduler = Scheduler(ModuleBudget(token_budget=4096, time_budget=4.5, web_calls=32))
        blackboard.post(
            "bootstrap",
            {
                "prompt": prompt,
                "understanding": understanding_summary,
                "memory_topics": list(memory_topics),
            },
        )
        scheduler.start_round("normalize", blackboard)
        normalised_intent = self._planner.normalise_intent(prompt)
        blackboard.context_graph["intent"] = normalised_intent
        blackboard.post("intent", {"value": normalised_intent})
        if scheduler.time_exceeded():
            return self._finalise(blackboard, "", [], 0.2, None, None, [])

        scheduler.start_round("plan", blackboard)
        plan = prior_plan or self._planner.build_plan(normalised_intent, context_terms)
        blackboard.plan = plan
        blackboard.thought_graph.add_node(ThoughtNode("intent", "Intent", normalised_intent))
        for node in plan.to_nodes():
            blackboard.thought_graph.add_node(node)
        scheduler.consume(tokens=len(plan.steps) * 12)

        scheduler.start_round("retrieve", blackboard)
        evidence = self._retrieval.search(plan, context_terms)
        blackboard.evidence.extend(evidence)
        for item in evidence:
            blackboard.thought_graph.link("intent", item.source_id, weight=item.strength)
        scheduler.consume(tokens=len(evidence) * 25, web=len(evidence))

        scheduler.start_round("world-model", blackboard)
        events = self._knowledge_graph.update_from_evidence(evidence)
        blackboard.timeline.extend(events)
        blackboard.argument_graph["claims"] = [event.to_dict() for event in events]
        scheduler.consume(tokens=len(events) * 10)

        scheduler.start_round("draft", blackboard)
        style_choice = self._style.select_profile(plan, context_terms)
        blackboard.style = style_choice
        draft = self._planner.compose_draft(plan, evidence, style_choice)
        blackboard.add_draft(draft)

        scheduler.start_round("coherence", blackboard)
        coherence = self._coherence.score(draft)
        blackboard.coherence = coherence
        blackboard.scores["coherence"] = coherence.score

        scheduler.start_round("critics", blackboard)
        critic_findings = self._critics.review(draft, evidence, plan)
        repairs = self._planner.apply_repairs(draft, critic_findings, coherence)
        if repairs and repairs != draft:
            draft = repairs
            blackboard.add_draft(draft)
        scheduler.consume(tokens=128)

        scheduler.start_round("evaluation", blackboard)
        evaluation = self._evaluation.evaluate(draft, plan, evidence, coherence, critic_findings)
        blackboard.evaluations = evaluation
        blackboard.scores.update(evaluation.scores)
        confidence = self._calibrate_confidence(evaluation)

        citations = [item.citation() for item in evidence]
        result = self._finalise(
            blackboard,
            draft,
            citations,
            confidence,
            coherence,
            style_choice,
            critic_findings,
            evaluation=evaluation,
        )
        return result

    # Internal helpers -------------------------------------------------
    def _finalise(
        self,
        blackboard: Blackboard,
        draft: str,
        citations: List[str],
        confidence: float,
        coherence: Optional[CoherenceReport],
        style: Optional[StyleSelection],
        critics: List[CriticFinding],
        *,
        evaluation: Optional[EvaluationReport] = None,
    ) -> OrchestratorResult:
        trace_payload = {
            "plan": blackboard.plan.to_dict() if blackboard.plan else None,
            "evidence": [item.to_dict() for item in blackboard.evidence],
            "timeline": [event.to_dict() for event in blackboard.timeline],
            "scores": blackboard.scores,
            "trace": blackboard.trace,
        }
        try:
            path = Path(self._trace_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                json.dump(trace_payload, handle, indent=2)
            trace_path = str(path)
        except Exception as error:  # pragma: no cover - defensive logging
            blackboard.post(
                "trace_error",
                {"error": f"{type(error).__name__}: {error}"},
            )
            trace_path = None
        return OrchestratorResult(
            final_text=draft,
            citations=citations,
            confidence=confidence,
            blackboard=blackboard,
            critics=critics,
            evaluation=evaluation or EvaluationReport.empty(),
            coherence=coherence,
            style=style,
            trace_path=trace_path,
        )

    @staticmethod
    def _calibrate_confidence(report: EvaluationReport) -> float:
        fact = report.scores.get("fact", 0.0)
        coherence = report.scores.get("coherence", 0.0)
        helpfulness = report.scores.get("helpfulness", 0.0)
        penalties = report.scores.get("policy_risk", 0.0) + report.scores.get("contradiction", 0.0)
        base = 0.4 * fact + 0.3 * coherence + 0.2 * helpfulness - 0.3 * penalties
        return max(0.05, min(0.98, base))
