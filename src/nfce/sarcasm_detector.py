"""Lightweight sarcasm heuristic."""
from __future__ import annotations


def is_sarcastic(text: str) -> bool:
    lowered = text.lower()
    return "yeah right" in lowered or "sure" in lowered


__all__ = ["is_sarcastic"]
