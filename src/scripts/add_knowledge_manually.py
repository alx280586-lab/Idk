"""Add a single knowledge node manually."""
from __future__ import annotations

from nfce.knowledge_graph.node import Node, PolysemyVariant, RelationshipBundle, FieldSignature
from nfce.knowledge_graph.graph import InMemoryGraph


def main():
    graph = InMemoryGraph()
    node = Node(
        node_id="manual-1",
        title="custom",
        primary_definition="User provided node",
        scientific_subnodes={},
        metaphorical_subnodes={},
        linguistic_properties={},
        polysemy_bundles=[PolysemyVariant(variant_id=1, context_signature="custom", field_region="user")],
        emotional_vectors={},
        contradiction_signatures=[],
        relationship_bundle=RelationshipBundle(),
        semantic_field_signature=FieldSignature(coordinates=[0.0], energy=0.1, sparsity=0.95),
        examples=[],
        reasoning_hooks={},
        sources=["manual"],
    )
    graph.add_node(node)
    graph.save()
    print("Saved manual node to graph store")


if __name__ == "__main__":
    main()
