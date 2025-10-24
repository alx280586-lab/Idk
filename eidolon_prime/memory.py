"""Simple in-memory knowledge graph representation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


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

    def summarize(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for entry in self.entries:
            summary[entry.topic] = summary.get(entry.topic, 0) + 1
        return summary

    def latest_by_provenance(self, provenance: str, limit: int = 3) -> List[MemoryEntry]:
        matches = [entry for entry in self.entries if entry.provenance == provenance]
        return matches[-limit:]
