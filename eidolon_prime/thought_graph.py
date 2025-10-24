"""Graph utilities for reasoning traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ThoughtNode:
    identifier: str
    label: str
    content: str
    metadata: Optional[Dict[str, object]] = None

    def to_dict(self) -> Dict[str, object]:
        payload = {
            "id": self.identifier,
            "label": self.label,
            "content": self.content,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass
class ThoughtEdge:
    source: str
    target: str
    weight: float

    def to_dict(self) -> Dict[str, object]:
        return {"source": self.source, "target": self.target, "weight": self.weight}


@dataclass
class ThoughtGraph:
    nodes: Dict[str, ThoughtNode] = field(default_factory=dict)
    edges: List[ThoughtEdge] = field(default_factory=list)

    def add_node(self, node: ThoughtNode) -> None:
        self.nodes[node.identifier] = node

    def link(self, source: str, target: str, weight: float = 1.0) -> None:
        self.edges.append(ThoughtEdge(source=source, target=target, weight=weight))

    def to_dict(self) -> Dict[str, object]:
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
        }
