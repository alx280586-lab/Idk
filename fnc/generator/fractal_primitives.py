"""Fractal primitive functions used by the generator."""
from __future__ import annotations

import math
from typing import Tuple

import torch


def perlin_noise(coords: torch.Tensor, frequency: float = 1.0) -> torch.Tensor:
    """Placeholder Perlin noise using sin/cos projections."""
    return torch.sin(coords * frequency) + torch.cos(coords * frequency / 2)


def fractional_brownian_motion(coords: torch.Tensor, octaves: int = 3) -> torch.Tensor:
    """Approximate fBm by summing scaled noise octaves."""
    value = torch.zeros_like(coords)
    amplitude = 1.0
    for octave in range(octaves):
        value += amplitude * torch.sin(coords * (2 ** octave))
        amplitude *= 0.5
    return value


def low_discrepancy_sequence(index: int, base: int = 2) -> float:
    """Return the Halton sequence value for *index* and *base*."""
    result = 0.0
    f = 1.0 / base
    i = index
    while i > 0:
        result = result + f * (i % base)
        i = i // base
        f = f / base
    return result


__all__ = ["perlin_noise", "fractional_brownian_motion", "low_discrepancy_sequence"]
