"""Assigns emotional tone to inputs and nodes."""
from __future__ import annotations

from typing import Dict


def score_text(text: str) -> Dict[str, float]:
    # placeholder lexicon-based scoring
    base = {
        "seriousness": 0.5,
        "awe": 0.2,
        "joy": 0.1,
        "sadness": 0.1,
    }
    if "!" in text:
        base["joy"] += 0.2
    return base


__all__ = ["score_text"]
