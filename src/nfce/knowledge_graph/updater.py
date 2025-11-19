"""Runtime editing utilities for graph nodes."""
from __future__ import annotations

from typing import Callable
from .node import Node


def update_node(node: Node, update_fn: Callable[[Node], Node]) -> Node:
    updated = update_fn(node)
    updated.version = f"{float(node.version) + 0.1:.1f}" if node.version.replace('.', '').isdigit() else node.version
    return updated


__all__ = ["update_node"]
