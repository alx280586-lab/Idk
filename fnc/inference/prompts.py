"""Prompt utilities for inference demos."""
from __future__ import annotations

from typing import List


def load_seed_prompts() -> List[str]:
    return [
        "Write a haiku about procedural weights.",
        "Explain fractal neural compression in simple terms.",
    ]


__all__ = ["load_seed_prompts"]
