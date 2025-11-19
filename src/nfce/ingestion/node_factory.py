"""Create Node objects from parsed content."""
from __future__ import annotations

from typing import Dict, List
from datetime import datetime
from ..knowledge_graph.node import Node, PolysemyVariant, RelationshipBundle, ContradictionPattern, FieldSignature


def create_node(node_id: str, title: str, summary: Dict, links: List[Dict], categories: List[str], sources: List[str]) -> Node:
    polysemy = [PolysemyVariant(**variant) for variant in summary.get("polysemy", [])]
    relationships = RelationshipBundle(
        mentions=[{"type": link.get("type", "mentions"), "target": link["target"]} for link in links],
        related_to=[],
        member_of=[{"type": "member_of", "target": cat} for cat in categories],
        infobox_relations=[],
    )
    node = Node(
        node_id=node_id,
        title=title,
        primary_definition=summary.get("primary_definition", ""),
        scientific_subnodes=summary.get("scientific_subnodes", {}),
        metaphorical_subnodes=summary.get("metaphorical_subnodes", {}),
        linguistic_properties=summary.get("linguistic_properties", {}),
        polysemy_bundles=polysemy,
        emotional_vectors=summary.get("emotional_vectors", {}),
        contradiction_signatures=[ContradictionPattern(description=pat) for pat in summary.get("contradiction_signatures", [])],
        relationship_bundle=relationships,
        semantic_field_signature=FieldSignature(coordinates=summary.get("field_coordinates", []), energy=1.0, sparsity=0.9),
        examples=summary.get("examples", []),
        reasoning_hooks=summary.get("reasoning_hooks", {}),
        creation_timestamp=datetime.utcnow(),
        sources=sources,
    )
    return node


__all__ = ["create_node"]
