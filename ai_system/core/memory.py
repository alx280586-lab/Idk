"""Long-term and episodic memory structures for the organic scripting AI."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, Iterable, List


@dataclass
class MemoryTrace:
    """Represents a single memory entry."""

    context: str
    response: str
    score: float
    tags: List[str] = field(default_factory=list)


class EpisodicMemory:
    """Short-term memory buffer prioritizing recent experience."""

    def __init__(self, limit: int = 128) -> None:
        self._limit = limit
        self._buffer: Deque[MemoryTrace] = deque(maxlen=limit)

    def record(self, trace: MemoryTrace) -> None:
        self._buffer.append(trace)

    def recall(self, tag: str | None = None) -> List[MemoryTrace]:
        if tag is None:
            return list(self._buffer)
        return [trace for trace in self._buffer if tag in trace.tags]


class KnowledgeBase:
    """File-backed knowledge store built from curated scripts."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def store(self, identifier: str, content: str) -> Path:
        path = self.root / f"{identifier}.md"
        path.write_text(content)
        return path

    def load(self, identifier: str) -> str:
        path = self.root / f"{identifier}.md"
        if not path.exists():
            raise FileNotFoundError(identifier)
        return path.read_text()

    def search(self, keywords: Iterable[str]) -> Dict[str, str]:
        results: Dict[str, str] = {}
        for file in self.root.glob("*.md"):
            text = file.read_text()
            if all(keyword.lower() in text.lower() for keyword in keywords):
                results[file.stem] = text
        return results
