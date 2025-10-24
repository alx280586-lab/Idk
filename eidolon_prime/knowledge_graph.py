"""Typed knowledge graph used to ground reasoning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List
import time

from .retrieval import RetrievedEvidence


@dataclass
class WorldEvent:
    """Represents an entity or claim captured in the knowledge graph."""

    subject: str
    predicate: str
    obj: str
    timestamp: float
    source: str
    confidence: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.obj,
            "timestamp": self.timestamp,
            "source": self.source,
            "confidence": self.confidence,
        }


class KnowledgeGraph:
    """Maintains typed relations and temporal tape."""

    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, object]] = {}
        self._events: List[WorldEvent] = []

    def update_from_evidence(self, evidence: Iterable[RetrievedEvidence]) -> List[WorldEvent]:
        events: List[WorldEvent] = []
        for item in evidence:
            subject = item.source_id.split("::")[0]
            predicate = "supports"
            event = WorldEvent(
                subject=subject,
                predicate=predicate,
                obj=item.summary,
                timestamp=time.time(),
                source=item.provenance,
                confidence=min(1.0, max(0.05, item.strength)),
            )
            self._events.append(event)
            self._nodes.setdefault(subject, {"last_seen": event.timestamp})
            self._nodes[subject]["last_confidence"] = event.confidence
            events.append(event)
        return events

    def recent_events(self, limit: int = 5) -> List[WorldEvent]:
        return self._events[-limit:]

    def describe(self) -> Dict[str, object]:
        return {"nodes": list(self._nodes.keys()), "events": [event.to_dict() for event in self._events]}
