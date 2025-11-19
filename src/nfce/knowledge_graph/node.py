"""Pydantic models for NFCE Knowledge Graph nodes."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class PolysemyVariant(BaseModel):
    variant_id: int
    context_signature: str
    field_region: str
    embedding: Optional[List[float]] = None


class ContradictionPattern(BaseModel):
    description: str
    resolution_hint: Optional[str] = None


class Relationship(BaseModel):
    type: str
    target: str


class RelationshipBundle(BaseModel):
    mentions: List[Relationship] = Field(default_factory=list)
    related_to: List[Relationship] = Field(default_factory=list)
    member_of: List[Relationship] = Field(default_factory=list)
    infobox_relations: List[Relationship] = Field(default_factory=list)


class FieldSignature(BaseModel):
    coordinates: List[float] = Field(default_factory=list)
    energy: float = 0.0
    sparsity: float = 0.0


class Node(BaseModel):
    node_id: str
    title: str
    primary_definition: str
    scientific_subnodes: Optional[Dict] = None
    metaphorical_subnodes: Optional[Dict] = None
    linguistic_properties: Dict
    polysemy_bundles: List[PolysemyVariant]
    emotional_vectors: Dict[str, float]
    contradiction_signatures: List[ContradictionPattern]
    relationship_bundle: RelationshipBundle
    semantic_field_signature: FieldSignature
    examples: List[str]
    reasoning_hooks: Dict[str, List[str]]
    version: str = "1.0"
    creation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: List[str] = Field(default_factory=list)


__all__ = [
    "Node",
    "PolysemyVariant",
    "ContradictionPattern",
    "Relationship",
    "RelationshipBundle",
    "FieldSignature",
]
