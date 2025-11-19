"""Interactive chat demo placeholder."""
from __future__ import annotations

from nfce.reasoning_engine import run_inference
from nfce.knowledge_graph.node import Node, PolysemyVariant, RelationshipBundle, FieldSignature


def main():
    dummy_node = Node(
        node_id="1",
        title="gravity",
        primary_definition="Force attracting bodies",
        scientific_subnodes={},
        metaphorical_subnodes={},
        linguistic_properties={},
        polysemy_bundles=[PolysemyVariant(variant_id=1, context_signature="physics", field_region="core")],
        emotional_vectors={"seriousness": 0.8},
        contradiction_signatures=[],
        relationship_bundle=RelationshipBundle(),
        semantic_field_signature=FieldSignature(coordinates=[0.1, 0.2], energy=1.0, sparsity=0.9),
        examples=["Gravity pulls objects"],
        reasoning_hooks={},
        sources=["demo"],
    )
    response = run_inference("Explain gravity", [dummy_node])
    print(response)


if __name__ == "__main__":
    main()
