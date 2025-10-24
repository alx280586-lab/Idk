"""Retrieval utilities combining lexical search and provenance scoring."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence
from collections import Counter
import math

from .memory import MemoryWeb, MemoryEntry


@dataclass
class RetrievedEvidence:
    """Represents a single evidence fragment."""

    text: str
    source_id: str
    provenance: str
    timestamp: float
    strength: float
    summary: str
    tags: List[str]

    def citation(self) -> str:
        return f"{self.provenance} ({self.timestamp:.0f})"

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "source_id": self.source_id,
            "provenance": self.provenance,
            "timestamp": self.timestamp,
            "strength": self.strength,
            "summary": self.summary,
            "tags": list(self.tags),
        }


class RetrievalManager:
    """Combines BM25-style scoring with provenance heuristics."""

    def __init__(self, memory: MemoryWeb) -> None:
        self._memory = memory

    def search(self, plan, focus_terms: Sequence[str]) -> List[RetrievedEvidence]:
        candidates = self._memory.search(" ".join(focus_terms) or plan.goal, limit=20)
        if not candidates:
            return []
        idf = self._idf_scores(candidates)
        evidence: List[RetrievedEvidence] = []
        for entry in candidates:
            weight = self._bm25(entry, focus_terms, idf)
            provenance = f"{entry.topic} @ {entry.timestamp.isoformat()}"
            summary_source = getattr(entry, "summary", None)
            summary = summary_source if summary_source else entry.content[:140]
            evidence.append(
                RetrievedEvidence(
                    text=entry.content,
                    source_id=entry.topic,
                    provenance=provenance,
                    timestamp=entry.timestamp.timestamp(),
                    strength=weight * entry.confidence,
                    summary=summary,
                    tags=self._tags_for(entry, plan, focus_terms),
                )
            )
        evidence.sort(key=lambda item: item.strength, reverse=True)
        return evidence[:12]

    # Internal helpers -------------------------------------------------
    def _idf_scores(self, entries: Sequence[MemoryEntry]) -> Counter:
        doc_count = len(entries)
        term_counts: Counter = Counter()
        for entry in entries:
            tokens = set(entry.content.lower().split())
            term_counts.update(tokens)
        return Counter({term: math.log((doc_count + 1) / (count + 1)) + 1 for term, count in term_counts.items()})

    def _bm25(self, entry: MemoryEntry, terms: Sequence[str], idf: Counter) -> float:
        if not terms:
            return entry.confidence
        tokens = entry.content.lower().split()
        counts = Counter(tokens)
        avg_len = max(1.0, sum(len(e.content.split()) for e in [entry]) / 1)
        score = 0.0
        k1 = 1.6
        b = 0.75
        doc_len = len(tokens)
        for term in terms:
            lowered = term.lower()
            freq = counts.get(lowered, 0)
            if freq == 0:
                continue
            numerator = freq * (k1 + 1)
            denominator = freq + k1 * (1 - b + b * (doc_len / avg_len))
            score += idf.get(lowered, 1.0) * (numerator / denominator)
        if entry.confidence < 0.4:
            score *= 0.6
        return score

    def _tags_for(self, entry: MemoryEntry, plan, terms: Sequence[str]) -> List[str]:
        tags: List[str] = []
        for step in plan.steps:
            for requirement in step.evidence_requirements:
                if any(token in entry.content.lower() for token in terms):
                    tags.append(requirement)
        if not tags:
            tags.append(f"context::{entry.topic}")
        return tags
