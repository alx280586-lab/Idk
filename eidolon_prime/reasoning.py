"""Reasoning profile helpers that shape deliberation output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .comprehension import MessageUnderstanding
from .knowledge import KnowledgeGapReport
from .memory import MemoryEntry
from .synthetic import SyntheticThoughtPlan
from .orchestrator import OrchestratorResult
from .web_growth import AutoTrainingReport, AutoTrainingHighlight

try:  # pragma: no cover - optional import for typing only
    from .forge import ExperimentResult
except ImportError:  # pragma: no cover - fallback when forge not available at import time
    ExperimentResult = object  # type: ignore[misc, assignment]

_SMALLTALK_TERMS = {
    "hello",
    "hi",
    "hey",
    "hiya",
    "yo",
    "greetings",
    "morning",
    "evening",
    "afternoon",
    "today",
    "doing",
    "friend",
    "buddy",
    "thanks",
    "thank",
}

_ANALYTIC_DOMAINS = {
    "reasoning",
    "analysis",
    "cortex",
    "synthetic",
    "speech_practice",
    "interaction",
    "autonomy",
    "curriculum",
}


@dataclass
class ReasoningProfile:
    """Tracks reasoning tendencies influenced by comprehension and training."""

    _domain_bias: Dict[str, float] = field(default_factory=dict)
    _focus_history: List[str] = field(default_factory=list)
    _training_history: List[str] = field(default_factory=list)
    last_summary: str = ""

    def refine_related(
        self,
        prompt: str,
        understanding: Optional[MessageUnderstanding],
        related: Sequence[MemoryEntry],
    ) -> List[MemoryEntry]:
        """Return related memories reordered according to current tendencies."""

        refined = list(related)
        informative_terms = self._informative_terms(understanding)
        if understanding and not informative_terms:
            refined = self._prioritise_generic_domains(refined)
        elif informative_terms:
            refined = sorted(
                refined,
                key=lambda entry: (
                    self._match_score(entry, informative_terms),
                    self._domain_bias_value(entry),
                ),
                reverse=True,
            )
        self._observe_prompt(prompt, understanding, refined)
        return refined

    def observe_training(self, report: AutoTrainingReport) -> None:
        """Update internal tendencies after an autonomous training batch."""

        bonus = (report.average_trust - 0.5) * 0.1
        if report.highlights:
            for highlight in report.highlights:
                domain = self._domain_key(highlight.topic)
                tier_bonus = self._tier_bonus(highlight)
                self._domain_bias[domain] = max(
                    0.0,
                    self._domain_bias.get(domain, 0.0) + 0.03 + tier_bonus + bonus,
                )
                snippet = f"{highlight.topic} ← {highlight.source} (tier {highlight.tier})"
                self._training_history.append(snippet)
        else:
            self._training_history.append(
                f"Focused crawl on {report.focus or 'general knowledge'} (score {report.quiz_score:.2f})."
            )
        self._trim_histories()
        self._decay_bias()

    def register_foundation(self, description: str) -> None:
        """Record foundational knowledge that shapes early reasoning."""

        if description:
            self._training_history.append(description)
            self._trim_histories()

    def compose_summary(
        self,
        prompt: str,
        related: Sequence[MemoryEntry],
        experiments: Sequence[ExperimentResult],
        understanding: Optional[MessageUnderstanding] = None,
        plan: Optional[SyntheticThoughtPlan] = None,
        gaps: Optional[KnowledgeGapReport] = None,
        orchestration: Optional[OrchestratorResult] = None,
    ) -> str:
        """Create a multi-paragraph reasoning explanation."""

        informative_terms = self._informative_terms(understanding)
        if informative_terms:
            focus_text = ", ".join(informative_terms[:5])
            first_sentence = (
                "I analysed every token in your message and locked onto "
                f"the substantive anchors {focus_text}."
            )
        else:
            first_sentence = (
                "Your message resembled a social preface, so I temporarily suppressed "
                "domain-specific habits (like defaulting to Roblox) and rebuilt the "
                "focus from scratch."
            )
        if related:
            domain_counts = self._domain_counts(related)
            top_domain, count = domain_counts[0]
            first_sentence += (
                f" That weighting elevated the {top_domain} cluster, supported by {count} "
                "relevant memories."
            )
        else:
            first_sentence += (
                " There were no direct memory hits, so I prepared to lean on autonomous "
                "harvests and new simulations."
            )
        experiment_sentence = self._summarise_experiments(experiments)
        plan_sentence = self._summarise_plan(plan)
        training_sentence = self._summarise_training_influence()
        gap_sentence = self._summarise_gaps(gaps, understanding)
        orchestration_sentence = self._summarise_orchestration(orchestration)
        second_paragraph_parts = [
            experiment_sentence,
            plan_sentence,
            training_sentence,
            gap_sentence,
            orchestration_sentence,
        ]
        second_paragraph = " ".join(part for part in second_paragraph_parts if part)
        paragraphs = [first_sentence]
        if second_paragraph:
            paragraphs.append(second_paragraph)
        summary = "\n\n".join(paragraphs)
        self.last_summary = summary
        return summary

    def register_gap_resolution(self, term: str, sources: Sequence[str]) -> None:
        """Record that a vocabulary gap has been resolved."""

        if not term:
            return
        description = term
        if sources:
            description += f" via {', '.join(sources[:2])}"
        self._training_history.append(f"Resolved vocabulary: {description}")
        self._trim_histories()

    def bias_snapshot(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Return the most emphasised reasoning domains."""

        return sorted(
            ((domain, weight) for domain, weight in self._domain_bias.items() if weight > 0.0),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]

    def recent_training(self, limit: int = 3) -> List[str]:
        """Return recent training snippets that influenced reasoning."""

        return self._training_history[-limit:]

    # Internal helpers -------------------------------------------------

    def _observe_prompt(
        self,
        prompt: str,
        understanding: Optional[MessageUnderstanding],
        related: Sequence[MemoryEntry],
    ) -> None:
        if understanding:
            focus = understanding.focus_text()
            if focus:
                self._focus_history.append(focus)
        else:
            self._focus_history.append(prompt[:120])
        for entry in related:
            domain = self._domain_key(entry.topic)
            increment = 0.02
            if domain in _ANALYTIC_DOMAINS:
                increment += 0.02
            self._domain_bias[domain] = self._domain_bias.get(domain, 0.0) + increment
        self._trim_histories()
        self._decay_bias()

    def _informative_terms(self, understanding: Optional[MessageUnderstanding]) -> List[str]:
        if not understanding:
            return []
        terms = [term for term in understanding.focus_terms if term not in _SMALLTALK_TERMS]
        if not terms:
            terms = [
                pair
                for pair in understanding.focus_pairs
                if not all(token in _SMALLTALK_TERMS for token in pair.split())
            ]
        return terms

    def _prioritise_generic_domains(self, related: Sequence[MemoryEntry]) -> List[MemoryEntry]:
        generic_entries: List[MemoryEntry] = []
        specialised_entries: List[MemoryEntry] = []
        for entry in related:
            if "roblox" in entry.topic.lower():
                specialised_entries.append(entry)
                continue
            domain = self._domain_key(entry.topic)
            if domain in _ANALYTIC_DOMAINS or "general" in domain:
                generic_entries.append(entry)
            else:
                specialised_entries.append(entry)
        return generic_entries + specialised_entries

    def _domain_counts(self, related: Sequence[MemoryEntry]) -> List[Tuple[str, int]]:
        counts: Dict[str, int] = {}
        for entry in related:
            domain = self._domain_key(entry.topic)
            counts[domain] = counts.get(domain, 0) + 1
        return sorted(counts.items(), key=lambda item: item[1], reverse=True)

    def _match_score(self, entry: MemoryEntry, terms: Sequence[str]) -> float:
        entry_tokens = self._tokenize_entry(entry)
        return sum(1.0 for term in terms if term in entry_tokens)

    def _domain_bias_value(self, entry: MemoryEntry) -> float:
        return self._domain_bias.get(self._domain_key(entry.topic), 0.0)

    def _tokenize_entry(self, entry: MemoryEntry) -> set:
        return {
            token
            for token in f"{entry.topic} {entry.content}".lower().replace("::", " ").split()
            if token
        }

    def _domain_key(self, topic: str) -> str:
        return topic.split("::")[0].lower()

    def _tier_bonus(self, highlight: AutoTrainingHighlight) -> float:
        tier = (highlight.tier or "").upper()
        if tier == "S":
            return 0.07
        if tier == "A":
            return 0.05
        if tier == "B":
            return 0.04
        if tier == "C":
            return 0.03
        return 0.02

    def _summarise_experiments(self, experiments: Sequence[ExperimentResult]) -> str:
        total = len(experiments)
        if not total:
            return ""
        successes = sum(1 for result in experiments if getattr(result, "success", False))
        return (
            f"I ran {total} quick experiments in the Forge and {successes} passed, "
            "reinforcing the hypotheses before writing anything."
        )

    def _summarise_plan(self, plan: Optional[SyntheticThoughtPlan]) -> str:
        if not plan:
            return ""
        modules = ", ".join(trace.module for trace in plan.module_traces[:3])
        outline = plan.outline[0] if plan.outline else "a verification loop"
        return (
            f"The synthetic plan activated {modules or 'core modules'} and staged {outline}"
            " to keep reasoning sequential."
        )

    def _summarise_training_influence(self) -> str:
        snippets = self.recent_training(2)
        if not snippets:
            return "I'm still gathering extended practice runs so upcoming answers stay balanced."
        joined = "; ".join(snippets)
        return f"Recent autonomous study nudged my tendencies, most notably: {joined}."

    def _summarise_gaps(
        self,
        gaps: Optional[KnowledgeGapReport],
        understanding: Optional[MessageUnderstanding],
    ) -> str:
        if not gaps:
            return ""
        resolved = gaps.resolved_terms()
        unresolved = gaps.unresolved_terms()
        messages: List[str] = []
        if resolved:
            display = ", ".join(resolved[:3])
            messages.append(f"New vocabulary locked in: {display}.")
        if understanding and understanding.unknown_terms and not unresolved:
            checked = ", ".join(understanding.unknown_terms[:3])
            messages.append(f"Every unfamiliar term you used has been researched ({checked}).")
        if unresolved:
            pending = ", ".join(unresolved[:2])
            messages.append(f"Queued additional research for: {pending}.")
        return " ".join(messages)

    def _summarise_orchestration(
        self, orchestration: Optional[OrchestratorResult]
    ) -> str:
        if not orchestration:
            return ""
        parts: List[str] = []
        if orchestration.coherence:
            parts.append(
                f"Entity grid coherence {orchestration.coherence.score:.2f}"
            )
        if orchestration.citations:
            preview = ", ".join(orchestration.citations[:3])
            parts.append(f"Cited {len(orchestration.citations)} sources ({preview}).")
        parts.append(f"Confidence calibrated to {orchestration.confidence:.2f}.")
        return " ".join(parts)

    def _trim_histories(self) -> None:
        if len(self._focus_history) > 60:
            del self._focus_history[:-60]
        if len(self._training_history) > 60:
            del self._training_history[:-60]

    def _decay_bias(self) -> None:
        for domain, weight in list(self._domain_bias.items()):
            new_weight = weight * 0.985
            if new_weight < 0.001:
                self._domain_bias.pop(domain, None)
            else:
                self._domain_bias[domain] = new_weight


__all__ = ["ReasoningProfile"]
