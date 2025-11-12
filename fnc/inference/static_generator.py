"""Static weight bundles for hosting external LLM checkpoints."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, Tuple

import torch
import torch.nn as nn

from fnc.fnc_core.config import FNCConfig
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry

BlockSpec = Tuple[str, int, int, int, int]


class StaticWeightGenerator(nn.Module):
    """Generator facade that returns pre-computed weight blocks."""

    def __init__(self, weight_map: Dict[BlockSpec, torch.Tensor], coord_embed_dim: int = 64) -> None:
        super().__init__()
        self.coord_embed_dim = coord_embed_dim
        self.num_lod = 1
        self._weights: Dict[BlockSpec, torch.Tensor] = {
            tuple(spec): tensor.clone().detach() for spec, tensor in weight_map.items()
        }
        self._anchor = torch.zeros(1)

    @property
    def weights(self) -> Dict[BlockSpec, torch.Tensor]:
        return self._weights

    def forward(self, seed: torch.Tensor, coords: torch.Tensor, context: Dict) -> Dict[str, torch.Tensor]:
        spec = context.get("block_spec")
        if spec is None:
            raise KeyError("StaticWeightGenerator requires 'block_spec' in context")
        block = self._weights.get(tuple(spec))
        if block is None:
            available = ", ".join(str(k) for k in self._weights.keys())
            raise KeyError(f"No static weight available for spec {spec}; have: {available}")
        device = coords.device if isinstance(coords, torch.Tensor) else self._anchor.device
        weight = block.to(device)
        aux = {
            "lod_used": 1,
            "smoothness": float(weight.std().item()),
            "virtual_params": float(weight.numel()),
        }
        return {"weights": weight.unsqueeze(0), "aux": aux}


def _serialise_weights(weights: Dict[BlockSpec, torch.Tensor]) -> Dict[str, torch.Tensor]:
    return {str(spec): tensor.cpu() for spec, tensor in weights.items()}


def _deserialise_weights(payload: Dict[str, torch.Tensor]) -> Dict[BlockSpec, torch.Tensor]:
    return {tuple(ast.literal_eval(key)): tensor for key, tensor in payload.items()}


def save_static_bundle(
    path: Path,
    cfg: FNCConfig,
    generator: StaticWeightGenerator,
    seeds: SeedRegistry,
    precision: PrecisionPolicy,
    extras: Dict[str, object] | None = None,
) -> None:
    """Persist a static bundle containing config, weights, and runtime metadata."""

    serialised_extras: Dict[str, object] = {}
    if extras:
        for key, value in extras.items():
            if isinstance(value, torch.Tensor):
                serialised_extras[key] = value.cpu()
            else:
                serialised_extras[key] = value

    state = {
        "config": cfg.as_dict(),
        "weights": _serialise_weights(generator.weights),
        "precision": {"default_bits": precision.default_bits, "overrides": precision.overrides},
        "seeds": seeds.as_dict(),
        "extras": serialised_extras,
    }
    torch.save(state, path)


def load_static_bundle(
    path: Path,
) -> Tuple[FNCConfig, StaticWeightGenerator, SeedRegistry, PrecisionPolicy, Dict[str, object]]:
    """Load a previously exported static bundle."""

    state = torch.load(path, map_location="cpu")
    cfg = FNCConfig.from_dict(state["config"]) if "config" in state else FNCConfig()
    weights = _deserialise_weights(state.get("weights", {}))
    generator = StaticWeightGenerator(weights)
    precision_state = state.get("precision", {})
    precision = PrecisionPolicy(
        default_bits=precision_state.get("default_bits", cfg.generator.quant_policy.get("default_bits", 8)),
        overrides=precision_state.get("overrides"),
    )
    seeds = SeedRegistry(cfg.training.seed)
    if "seeds" in state:
        seeds.load_state(state["seeds"])
    extras = state.get("extras", {})
    if not isinstance(extras, dict):
        extras = {}
    return cfg, generator, seeds, precision, extras


__all__ = ["StaticWeightGenerator", "save_static_bundle", "load_static_bundle"]
