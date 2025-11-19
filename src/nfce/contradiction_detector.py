"""Simple contradiction detector placeholder."""
from __future__ import annotations


def detect_contradiction(statement: str) -> bool:
    return "not" in statement.lower() and "and" in statement.lower()


__all__ = ["detect_contradiction"]
