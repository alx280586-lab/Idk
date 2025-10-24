"""Knowledge gap tracking and resolution helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence

from .comprehension import MessageUnderstanding
from .memory import MemoryEntry, MemoryWeb
from .web_growth import AutoTrainingReport, AutoTrainingHighlight


_BASELINE_TERMS = {
    "hello",
    "hi",
    "thanks",
    "today",
    "friend",
    "economy",
    "roblox",
    "code",
    "coding",
    "game",
    "player",
    "balance",
    "design",
    "plan",
    "analysis",
    "training",
    "grammar",
    "language",
    "memory",
    "engine",
    "system",
}

_CODING_KEYWORDS = {
    "code",
    "coding",
    "script",
    "python",
    "lua",
    "function",
    "variable",
    "class",
    "module",
    "api",
    "compiler",
    "debug",
    "refactor",
    "architect",
    "design",
    "algorithm",
    "loop",
}


@dataclass
class KnowledgeGap:
    """Represents a vocabulary or concept gap detected from a message."""

    term: str
    reason: str
    resolved: bool = False
    sources: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class KnowledgeGapReport:
    """Collection of gaps alongside context flags."""

    gaps: List[KnowledgeGap] = field(default_factory=list)
    coding_terms: List[str] = field(default_factory=list)
    triggered_queries: List[str] = field(default_factory=list)

    def unresolved(self) -> List[KnowledgeGap]:
        return [gap for gap in self.gaps if not gap.resolved]

    def unresolved_terms(self) -> List[str]:
        return [gap.term for gap in self.unresolved()]

    def resolved_terms(self) -> List[str]:
        return [gap.term for gap in self.gaps if gap.resolved]


class KnowledgeGapMonitor:
    """Detects unfamiliar concepts and assists in storing resolutions."""

    def __init__(self, *, recheck_interval: int = 5) -> None:
        self._known_terms: set[str] = set(_BASELINE_TERMS)
        self._scheduled_reviews: Dict[str, int] = {}
        self._recheck_interval = max(2, recheck_interval)

    def evaluate(self, understanding: MessageUnderstanding, memory: MemoryWeb) -> KnowledgeGapReport:
        report = KnowledgeGapReport()
        tokens = [token for token in understanding.keywords if len(token) > 2]
        unique_tokens: List[str] = []
        for token in tokens:
            if token not in unique_tokens:
                unique_tokens.append(token)
        for token in unique_tokens:
            if token in self._known_terms:
                continue
            if self._memory_has(memory, token):
                self._known_terms.add(token)
                continue
            report.gaps.append(KnowledgeGap(term=token, reason="not stored in memory"))
        for sentence in understanding.sentences:
            cleaned = sentence.strip()
            if not cleaned:
                continue
            key = " ".join(cleaned.lower().split()[:6])
            if key in self._known_terms:
                continue
            if self._memory_has(memory, key):
                self._known_terms.add(key)
                continue
            if any(existing.term == cleaned for existing in report.gaps):
                continue
            report.gaps.append(KnowledgeGap(term=cleaned, reason="sentence meaning unanchored"))
        for term, countdown in list(self._scheduled_reviews.items()):
            countdown -= 1
            if countdown <= 0:
                if self._memory_has(memory, term):
                    report.gaps.append(
                        KnowledgeGap(
                            term=term,
                            reason="scheduled recheck",
                            resolved=True,
                            sources=["memory"],
                            summary="Revalidated stored definition.",
                        )
                    )
                    self._scheduled_reviews[term] = self._recheck_interval
                else:
                    report.gaps.append(KnowledgeGap(term=term, reason="scheduled recheck"))
                    self._scheduled_reviews[term] = self._recheck_interval
            else:
                self._scheduled_reviews[term] = countdown
        coding_terms = [token for token in unique_tokens if token in _CODING_KEYWORDS]
        if coding_terms:
            report.coding_terms.extend(coding_terms)
        if report.coding_terms:
            report.coding_terms = list(dict.fromkeys(report.coding_terms))
        return report

    def register_resolution(
        self,
        gap: KnowledgeGap,
        training_report: AutoTrainingReport,
        memory: MemoryWeb,
    ) -> KnowledgeGap:
        highlight_summary = self._highlight_summary(training_report.highlights)
        summary = (
            f"Resolved '{gap.term}' via autonomous training → {highlight_summary}"
            if highlight_summary
            else f"Resolved '{gap.term}' via autonomous training capturing {training_report.imported} entries."
        )
        memory.record(
            f"lexicon::{gap.term.lower().replace(' ', '_')}",
            summary,
            0.7,
            "knowledge_gap",
        )
        gap.resolved = True
        gap.summary = summary
        if training_report.highlights:
            gap.sources = [highlight.source for highlight in training_report.highlights[:3]]
        else:
            gap.sources = ["open_web"]
        lowered_term = gap.term.lower()
        self._known_terms.add(lowered_term)
        truncated = " ".join(lowered_term.split()[:6])
        if truncated:
            self._known_terms.add(truncated)
            self._scheduled_reviews[truncated] = self._recheck_interval
        self._scheduled_reviews[lowered_term] = self._recheck_interval
        return gap

    def sync_with_memory(self, memory: MemoryWeb) -> None:
        for entry in memory.entries:
            for token in self._tokenize(entry):
                self._known_terms.add(token)

    def _highlight_summary(self, highlights: Sequence[AutoTrainingHighlight]) -> str:
        if not highlights:
            return ""
        primary = highlights[0]
        detail = primary.summary or primary.insight
        return f"{primary.source} → {detail}".strip()

    def _memory_has(self, memory: MemoryWeb, query: str) -> bool:
        hits = memory.search(query, limit=1)
        if hits:
            return True
        for entry in memory.entries[-40:]:  # recent memories often include newest training
            if query.lower() in entry.content.lower() or query.lower() in entry.topic.lower():
                return True
        return False

    def _tokenize(self, entry: MemoryEntry) -> Iterable[str]:
        text = f"{entry.topic} {entry.content}".lower()
        for token in text.replace("::", " ").split():
            cleaned = token.strip(".,:;!?()[]{}")
            if len(cleaned) > 2:
                yield cleaned


__all__ = ["KnowledgeGap", "KnowledgeGapMonitor", "KnowledgeGapReport"]
