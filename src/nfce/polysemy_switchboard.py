"""Routes meanings to appropriate polysemy variants."""
from __future__ import annotations

from typing import List
from .knowledge_graph.node import Node


def select_variant(node: Node, context: str) -> Node:
    if not node.polysemy_bundles:
        return node
    # naive selection based on context signature keyword match
    for variant in node.polysemy_bundles:
        if variant.context_signature.lower() in context.lower():
            return node
    return node


__all__ = ["select_variant"]
