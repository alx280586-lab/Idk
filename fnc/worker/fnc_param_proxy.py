"""Lazy parameter proxy that triggers procedural generation on demand."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.caching import CacheInterface


@dataclass
class ProxyStats:
    hits: int = 0
    misses: int = 0
    materialisations: int = 0


class FNCParamProxy(nn.Module):
    """Wraps procedural generation of a parameter block."""

    def __init__(self, block_spec, seed, coord_encoder, generator, cache: CacheInterface, precision_ctrl: PrecisionPolicy) -> None:
        super().__init__()
        self.block_spec = block_spec
        self.seed = seed
        self.coord_encoder = coord_encoder
        self.generator = generator
        self.cache = cache
        self.precision = precision_ctrl
        self.stats_state = ProxyStats()

    @property
    def shape(self) -> tuple:
        rows, cols = int(self.block_spec[3]), int(self.block_spec[4])
        if cols == 1:
            return (rows,)
        return (rows, cols)

    def _target_numel(self) -> int:
        numel = 1
        for dim in self.shape:
            numel *= dim
        return numel

    def _reshape(self, tensor: torch.Tensor) -> torch.Tensor:
        target_shape = self.shape
        numel = self._target_numel()
        flat = tensor.view(-1)
        if numel <= flat.numel():
            reshaped = flat[:numel].view(*target_shape)
        else:
            padded = F.pad(flat, (0, numel - flat.numel()))
            reshaped = padded.view(*target_shape)
        return reshaped

    def materialize(self, device: Optional[torch.device] = None) -> torch.Tensor:
        key = tuple(self.block_spec)
        cached = self.cache.lookup(key)
        if cached is not None:
            self.stats_state.hits += 1
            return cached.to(device) if device else cached
        self.stats_state.misses += 1
        coords = self.coord_encoder.encode(self.block_spec)
        context: Dict = {
            "block_type": self.block_spec[0],
            "shape": tuple(self.shape),
            "lod": getattr(self.generator, "num_lod", 1),
            "block_spec": tuple(self.block_spec),
        }
        output = self.generator(self.seed, coords.unsqueeze(0), context)
        weights = output["weights"][0]
        quantized = self.precision.quantize(weights, self.block_spec[0], training=self.training)
        reshaped = self._reshape(quantized)
        cached = reshaped.detach()
        footprint = float(cached.numel() * max(1, self.precision.bits_for(self.block_spec[0])) / 8)
        self.cache.insert(key, cached, cost=footprint)
        if device:
            reshaped = reshaped.to(device)
        self.stats_state.materialisations += 1
        return reshaped

    def evict(self) -> None:
        key = tuple(self.block_spec)
        self.cache.remove(key)

    def pin(self) -> None:
        key = tuple(self.block_spec)
        self.cache.pin(key)

    def stats(self) -> Dict[str, int]:
        return {
            "hits": self.stats_state.hits,
            "misses": self.stats_state.misses,
            "materialisations": self.stats_state.materialisations,
        }


__all__ = ["FNCParamProxy"]
