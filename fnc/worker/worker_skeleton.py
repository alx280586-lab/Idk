"""Transformer worker skeleton using procedural parameters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch
import torch.nn as nn

from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.tensor_coords import CoordinateEncoder
from fnc.fnc_core.caching import CacheInterface
from fnc.fnc_core.seeds import SeedRegistry
from fnc.worker.fnc_param_proxy import FNCParamProxy
from fnc.worker.routing import simple_routing_plan
from fnc.worker.attention import procedural_attention_forward
from fnc.worker.mlp import procedural_mlp_forward
from fnc.worker.layernorm import procedural_layernorm


@dataclass
class WorkerConfig:
    d_model: int
    n_layers: int
    n_heads: int
    vocab_size: int
    max_seq_len: int


class FNCWorker(nn.Module):
    """Decoder-only transformer that relies on procedural parameter generation."""

    def __init__(
        self,
        cfg: WorkerConfig,
        generator,
        cache: CacheInterface,
        precision: PrecisionPolicy,
        seeds: SeedRegistry,
    ) -> None:
        super().__init__()
        self.cfg = cfg
        self.generator = generator
        self.cache = cache
        self.precision = precision
        self.seeds = seeds
        self.coord_encoder = CoordinateEncoder(embed_dim=generator.coord_embed_dim)
        self.embed_tokens = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.layers = nn.ModuleList([
            ProceduralBlock(
                layer_id=i,
                d_model=cfg.d_model,
                n_heads=cfg.n_heads,
                generator=generator,
                coord_encoder=self.coord_encoder,
                cache=cache,
                precision=precision,
                seeds=seeds,
            )
            for i in range(cfg.n_layers)
        ])
        ln_spec = ("ln_final", cfg.n_layers, 0, cfg.d_model, 1)
        lm_spec = ("lm_head", 0, 0, cfg.d_model, cfg.vocab_size)
        self.ln_proxy = FNCParamProxy(
            ln_spec,
            seeds.seed_for(ln_spec),
            self.coord_encoder,
            generator,
            cache,
            precision,
        )
        self.lm_proxy = FNCParamProxy(
            lm_spec,
            seeds.seed_for(lm_spec),
            self.coord_encoder,
            generator,
            cache,
            precision,
        )

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        if len(tokens.shape) == 1:
            tokens = tokens.view(1, tokens.shape[0])
        hidden = self.embed_tokens(tokens)
        for block, plan in zip(self.layers, simple_routing_plan(tokens.size(1), self.cfg.n_layers)):
            hidden = block(hidden, plan)
        ln_weight = self.ln_proxy.materialize()
        hidden = procedural_layernorm(hidden, ln_weight.squeeze())
        logits_weight = self.lm_proxy.materialize()
        logits = hidden @ logits_weight
        return logits


class ProceduralBlock(nn.Module):
    def __init__(self, layer_id: int, d_model: int, n_heads: int, generator, coord_encoder, cache, precision, seeds: SeedRegistry) -> None:
        super().__init__()
        self.layer_id = layer_id
        self.d_model = d_model
        self.n_heads = n_heads
        self.coord_encoder = coord_encoder
        self.generator = generator
        self.cache = cache
        self.precision = precision
        self.seeds = seeds
        self.q_proxy = self._create_proxy("attn_q_proj", d_model, d_model)
        self.k_proxy = self._create_proxy("attn_k_proj", d_model, d_model)
        self.v_proxy = self._create_proxy("attn_v_proj", d_model, d_model)
        self.o_proxy = self._create_proxy("attn_out_proj", d_model, d_model)
        self.ff1_proxy = self._create_proxy("mlp_fc1", d_model, d_model)
        self.ff2_proxy = self._create_proxy("mlp_fc2", d_model, d_model)

    def _create_proxy(self, block_type: str, rows: int, cols: int) -> FNCParamProxy:
        spec = (block_type, self.layer_id, 0, rows, cols)
        seed = self.seeds.seed_for(spec)
        return FNCParamProxy(spec, seed, self.coord_encoder, self.generator, self.cache, self.precision)

    def forward(self, hidden: torch.Tensor, plan: Dict) -> torch.Tensor:
        q = self.q_proxy.materialize()
        k = self.k_proxy.materialize()
        v = self.v_proxy.materialize()
        o = self.o_proxy.materialize()
        attn_out = procedural_attention_forward(hidden, q, k, v, o)
        hidden = hidden + attn_out
        ff1 = self.ff1_proxy.materialize()
        ff2 = self.ff2_proxy.materialize()
        mlp_out = procedural_mlp_forward(hidden, ff1, ff2)
        hidden = hidden + mlp_out
        return hidden


__all__ = ["FNCWorker", "WorkerConfig", "ProceduralBlock"]
