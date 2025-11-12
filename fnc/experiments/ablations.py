"""Experiment hooks for running ablation studies."""
from __future__ import annotations

from typing import Dict


ABLATIONS = {
    "noise_vs_spectral": "Compare IID noise against spectral field decoding.",
    "fixed_vs_learned_quant": "Evaluate fixed precision against learned policies.",
    "lod_progressive": "Assess progressive LoD unlocking vs static detail.",
    "cache_policies": "Benchmark LRU/LFU/ARC policies.",
}


def list_ablations() -> Dict[str, str]:
    return ABLATIONS


__all__ = ["list_ablations", "ABLATIONS"]
