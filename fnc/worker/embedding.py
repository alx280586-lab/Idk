"""Procedural token embeddings backed by the fractal generator."""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn

from fnc.fnc_core.caching import CacheInterface
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry
from fnc.fnc_core.tensor_coords import CoordinateEncoder
from fnc.worker.fnc_param_proxy import FNCParamProxy


class ProceduralEmbedding(nn.Module):
    """Generates token embeddings lazily via :class:`FNCParamProxy` instances."""

    def __init__(
        self,
        vocab_size: int,
        d_model: int,
        generator,
        coord_encoder: CoordinateEncoder,
        cache: CacheInterface,
        precision: PrecisionPolicy,
        seeds: SeedRegistry,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.generator = generator
        self.coord_encoder = coord_encoder
        self.cache = cache
        self.precision = precision
        self.seeds = seeds
        self._proxies: Dict[int, FNCParamProxy] = {}

    def _proxy_for(self, token_id: int) -> FNCParamProxy:
        if token_id not in self._proxies:
            spec = ("embed_token", int(token_id), 0, self.d_model, 1)
            seed = self.seeds.seed_for(spec)
            self._proxies[token_id] = FNCParamProxy(
                spec,
                seed,
                self.coord_encoder,
                self.generator,
                self.cache,
                self.precision,
            )
        return self._proxies[token_id]

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        if tokens.dim() == 1:
            tokens = tokens.unsqueeze(0)
        device = tokens.device
        batch, seq_len = tokens.shape
        flat_tokens = [int(t) for t in tokens.reshape(-1).tolist()]
        if not flat_tokens:
            return torch.zeros(batch, seq_len, self.d_model, device=device)

        ordered_tokens = list(dict.fromkeys(flat_tokens))
        vectors = []
        token_to_index: Dict[int, int] = {}
        for idx, token_int in enumerate(ordered_tokens):
            token_to_index[token_int] = idx
            proxy = self._proxy_for(token_int)
            vector = proxy.materialize(device=device).view(self.d_model)
            vectors.append(vector)

        embedded_rows = [vectors[token_to_index[token]] for token in flat_tokens]
        embedded = torch.stack(embedded_rows, dim=0).view(batch, seq_len, self.d_model)
        return embedded


__all__ = ["ProceduralEmbedding"]
