"""Training ground for ingesting user-provided knowledge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .memory import MemoryWeb, MemoryEntry


@dataclass
class TrainingRecord:
    """Receipt returned after storing new training information."""

    topic: str
    content: str
    entry: MemoryEntry
    total_entries: int

    def render(self) -> str:
        return (
            "Training update saved!\n"
            f"- Topic: {self.topic}\n"
            f"- Details: {self.content}\n"
            f"- Total training memories: {self.total_entries}"
        )


class TrainingGround:
    """Accepts explicit guidance and archives it into the memory web."""

    def __init__(self, memory: MemoryWeb) -> None:
        self._memory = memory

    def ingest(self, raw_text: str) -> TrainingRecord:
        topic, content = self._split(raw_text)
        entry = self._memory.record(topic, content, 0.9, "training")
        total_entries = len(self._memory.recall(topic))
        return TrainingRecord(topic, content, entry, total_entries)

    def _split(self, raw_text: str) -> Tuple[str, str]:
        payload = raw_text.strip()
        if not payload:
            raise ValueError("Training text cannot be empty.")
        if ":" in payload:
            topic, content = payload.split(":", 1)
            topic = topic.strip() or "training"
            content = content.strip()
        else:
            topic = "training"
            content = payload
        if not content:
            raise ValueError("Provide details after the topic.")
        return topic, content
