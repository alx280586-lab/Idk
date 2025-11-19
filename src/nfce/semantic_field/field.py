"""Semantic field representation using lightweight Fourier layers.

This is a compact placeholder implementation showing how a Fourier Neural
Operator-like block could be wired. The module is intentionally minimal
for portability within the exercise environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
import math
import torch
import torch.nn as nn
import torch.fft


@dataclass
class FieldState:
    """Container representing the semantic field at a timestep."""

    grid: torch.Tensor
    time: float


class SimpleFNOBlock(nn.Module):
    """A small Fourier layer inspired by FNO."""

    def __init__(self, in_channels: int, out_channels: int, modes: int):
        super().__init__()
        self.modes = modes
        scale = 1 / math.sqrt(in_channels)
        self.real = nn.Parameter(scale * torch.randn(in_channels, out_channels, modes))
        self.imag = nn.Parameter(scale * torch.randn(in_channels, out_channels, modes))
        self.pointwise = nn.Conv1d(in_channels, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, channels, grid)
        batch, channels, n = x.shape
        x_ft = torch.fft.rfft(x, dim=-1)
        out_ft = torch.zeros_like(x_ft)
        m = min(self.modes, x_ft.shape[-1])
        real = self.real[:, :, :m]
        imag = self.imag[:, :, :m]
        out_ft[:, :, :m] = (x_ft[:, :, :m].real @ real - x_ft[:, :, :m].imag @ imag) + 1j * (
            x_ft[:, :, :m].real @ imag + x_ft[:, :, :m].imag @ real
        )
        x_ifft = torch.fft.irfft(out_ft, n=x.shape[-1], dim=-1)
        return self.pointwise(x) + x_ifft


class SemanticField(nn.Module):
    """Neural approximation of the semantic field PDE."""

    def __init__(self, channels: int = 8, modes: int = 16, damping: float = 0.01):
        super().__init__()
        self.block1 = SimpleFNOBlock(channels, channels, modes)
        self.block2 = SimpleFNOBlock(channels, channels, modes)
        self.damping = damping

    def forward(self, state: FieldState, delta_t: float = 0.1) -> FieldState:
        # apply two-step propagation with damping
        x = state.grid
        x = torch.relu(self.block1(x))
        x = torch.relu(self.block2(x))
        x = x * math.exp(-self.damping * delta_t)
        return FieldState(grid=x, time=state.time + delta_t)


__all__ = ["SemanticField", "FieldState", "SimpleFNOBlock"]
