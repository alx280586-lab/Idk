"""Placeholders for optional fused CUDA kernels."""
from __future__ import annotations

from typing import Any


def fused_attention_stub(*_args: Any, **_kwargs: Any) -> None:
    """Placeholder fused kernel that should be implemented in CUDA."""
    raise NotImplementedError("fused_attention_stub requires CUDA implementation")


__all__ = ["fused_attention_stub"]
