"""Retrieval and refinement loop orchestrator."""
from __future__ import annotations

from typing import List
from .knowledge_graph.node import Node
from .knowledge_graph.retrieval import retrieve_by_title
from .polysemy_switchboard import select_variant


def run_loop(nodes: List[Node], query: str) -> List[Node]:
    candidates = retrieve_by_title(nodes, query)
    return [select_variant(node, query) for node in candidates]


__all__ = ["run_loop"]
