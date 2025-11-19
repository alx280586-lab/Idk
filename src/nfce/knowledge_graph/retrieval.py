"""Retrieval helpers combining symbolic and vector signals."""
from __future__ import annotations

from typing import List
from .node import Node


def retrieve_by_title(nodes: List[Node], query: str) -> List[Node]:
    return [n for n in nodes if query.lower() in n.title.lower()]


def retrieve_by_emotion(nodes: List[Node], emotion: str, threshold: float = 0.5) -> List[Node]:
    results = []
    for node in nodes:
        if node.emotional_vectors.get(emotion, 0.0) >= threshold:
            results.append(node)
    return results


__all__ = ["retrieve_by_title", "retrieve_by_emotion"]
