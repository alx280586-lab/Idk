"""High-level orchestration of inference."""
from __future__ import annotations

from typing import List
from .input_projector import project_text
from .semantic_field.field import SemanticField, FieldState
from .semantic_field.wave_propagator import propagate
from .retrieval_refinement_loop import run_loop
from .knowledge_graph.node import Node
from .conversational_module.generator import generate_response
from .conversational_module.style_adapter import apply_style


def run_inference(text: str, graph_nodes: List[Node], style: str = "concise") -> str:
    initial_state = project_text(text)
    field = SemanticField()
    evolved: FieldState = propagate(field, initial_state, steps=2)
    candidates = run_loop(graph_nodes, text)
    context = [node.primary_definition for node in candidates]
    response = generate_response(text, context)
    return apply_style(response, style)


__all__ = ["run_inference"]
