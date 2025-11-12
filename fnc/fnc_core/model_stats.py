"""Utilities to estimate virtual parameter counts for FNC workers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .config import FNCConfig


@dataclass
class ModelFootprint:
    """Summary of a worker's parameter budget and runtime footprint."""

    total_params: int
    virtual_params: int
    bytes_per_block: float
    cache_bytes: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "total_params": float(self.total_params),
            "virtual_params": float(self.virtual_params),
            "bytes_per_block": float(self.bytes_per_block),
            "cache_bytes": float(self.cache_bytes),
        }


def _format_int(value: int) -> int:
    return int(value)


def estimate_worker_params(cfg: FNCConfig) -> ModelFootprint:
    """Estimate the parameter budget for the configured worker.

    The worker skeleton instantiates four attention projections and two MLP
    projections per layer.  We treat the learned embedding, final layer norm,
    and output projection as additional blocks.  The *virtual* parameter count
    multiplies the physical parameters with the generator's level-of-detail
    setting, capturing how many distinct coefficients can be procedurally
    synthesised at inference time.
    """

    model = cfg.model
    generator = cfg.generator
    precision_bits = generator.quant_policy.get("default_bits", 8)
    d_model = model.d_model
    n_layers = model.n_layers
    vocab = model.vocab_size

    attn_block = 4 * d_model * d_model
    mlp_block = 2 * d_model * d_model
    layer_params = attn_block + mlp_block
    embed_params = d_model * vocab
    norm_params = d_model
    lm_params = d_model * vocab

    total_params = layer_params * n_layers + embed_params + norm_params + lm_params
    virtual_params = total_params * max(1, generator.num_lod)

    bytes_per_param = precision_bits / 8.0
    params_per_block = d_model * d_model
    bytes_per_block = params_per_block * bytes_per_param
    cache_bytes = bytes_per_block * 6  # q, k, v, out, mlp1, mlp2 for the active layer

    return ModelFootprint(
        total_params=_format_int(total_params),
        virtual_params=_format_int(virtual_params),
        bytes_per_block=bytes_per_block,
        cache_bytes=cache_bytes,
    )


__all__ = ["ModelFootprint", "estimate_worker_params"]
