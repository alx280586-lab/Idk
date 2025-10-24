"""Simple in-memory knowledge graph representation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, List, Dict, Any, Tuple


@dataclass
class MemoryEntry:
    """Representation of a single experience or belief."""

    timestamp: datetime
    topic: str
    content: str
    confidence: float
    provenance: str


@dataclass
class MemoryWeb:
    """Stores experiences and allows basic recall queries."""

    entries: List[MemoryEntry] = field(default_factory=list)

    def record(self, topic: str, content: str, confidence: float, provenance: str) -> MemoryEntry:
        entry = MemoryEntry(datetime.utcnow(), topic, content, confidence, provenance)
        self.entries.append(entry)
        return entry

    def recall(self, topic: str) -> List[MemoryEntry]:
        topic_lower = topic.lower()
        return [entry for entry in self.entries if topic_lower in entry.topic.lower()]

    def bulk_record(self, rows: Iterable[Tuple[str, str, float, str]]) -> int:
        """Insert multiple entries efficiently."""

        count = 0
        for topic, content, confidence, provenance in rows:
            self.record(topic, content, confidence, provenance)
            count += 1
        return count

    def summarize(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for entry in self.entries:
            summary[entry.topic] = summary.get(entry.topic, 0) + 1
        return summary

    def latest_by_provenance(self, provenance: str, limit: int = 3) -> List[MemoryEntry]:
        matches = [entry for entry in self.entries if entry.provenance == provenance]
        return matches[-limit:]

    def count_by_provenance(self, provenance: str) -> int:
        return sum(1 for entry in self.entries if entry.provenance == provenance)

    def search(self, text: str, limit: int = 5) -> List[MemoryEntry]:
        """Return memories ranked by keyword overlap and confidence."""

        query_tokens = _tokenize(text)
        if not query_tokens:
            return []
        scored: List[Tuple[float, MemoryEntry]] = []
        for entry in self.entries:
            entry_tokens = _tokenize(f"{entry.topic} {entry.content}")
            if not entry_tokens:
                continue
            overlap = len(query_tokens & entry_tokens)
            if overlap == 0:
                continue
            query_coverage = overlap / len(query_tokens)
            entry_coverage = overlap / len(entry_tokens)
            if overlap < 2 and query_coverage < 0.2:
                continue
            score = query_coverage * 0.55 + entry_coverage * 0.15 + entry.confidence * 0.3
            scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:limit]]


def _tokenize(text: str) -> set:
    return {token for token in text.lower().replace("::", " ").split() if token}
