"""Style adapter for conversational outputs."""
from __future__ import annotations


def apply_style(text: str, style: str = "concise") -> str:
    if style == "verbose":
        return text + " -- elaborated"
    if style == "curious":
        return text + "?"
    return text


__all__ = ["apply_style"]
