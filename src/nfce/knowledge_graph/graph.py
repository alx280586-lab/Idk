"""Hybrid Neo4j + FAISS graph store shim."""
from __future__ import annotations

from typing import Dict, List
from pathlib import Path
import json

from .node import Node


class InMemoryGraph:
    """Simplified graph store used for development and tests."""

    def __init__(self, storage_path: Path = Path("data/processed_graph/graph.json")):
        self.storage_path = storage_path
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Dict] = []
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def add_node(self, node: Node) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str, rel_type: str) -> None:
        self.edges.append({"source": source, "target": target, "type": rel_type})

    def save(self) -> None:
        data = {
            "nodes": {k: v.dict() for k, v in self.nodes.items()},
            "edges": self.edges,
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


__all__ = ["InMemoryGraph"]
