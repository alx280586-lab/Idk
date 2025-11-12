"""Attention primitives using procedurally generated weights."""
from __future__ import annotations

import torch


def procedural_attention_forward(
    hidden: torch.Tensor,
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    o: torch.Tensor,
) -> torch.Tensor:
    """Simplified attention computation for scaffolding."""
    dim = hidden.size(-1)
    q_proj = hidden @ q
    k_proj = hidden @ k
    v_proj = hidden @ v
    attn_scores = torch.softmax(q_proj @ k_proj.transpose(-2, -1) / dim**0.5, dim=-1)
    attn_out = attn_scores @ v_proj
    return attn_out @ o


__all__ = ["procedural_attention_forward"]
