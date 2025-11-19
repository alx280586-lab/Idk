"""Lightweight conversational generator stub."""
from __future__ import annotations

from typing import List


def generate_response(prompt: str, context: List[str] | None = None) -> str:
    prefix = "[NFCE Conversational]"
    context_text = " | ".join(context) if context else ""
    return f"{prefix} {prompt} {context_text}".strip()


__all__ = ["generate_response"]
