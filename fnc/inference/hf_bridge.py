"""Utilities for hosting Hugging Face checkpoints with the FNC runtime."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import torch

from fnc.fnc_core.config import FNCConfig
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry
from fnc.inference.static_generator import StaticWeightGenerator, save_static_bundle

BlockSpec = Tuple[str, int, int, int, int]


def _ensure_transformers():  # pragma: no cover - optional dependency
    try:
        import transformers  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "The 'transformers' package is required for Hugging Face interoperability."
        ) from exc
    return transformers


def _to_in_out(weight: torch.Tensor, expected_in: int) -> torch.Tensor:
    """Convert a linear weight to (in_features, out_features) layout."""

    if weight.shape[1] == expected_in:
        return weight.t()  # HF Conv1D uses (out, in)
    if weight.shape[0] == expected_in:
        return weight
    raise ValueError(f"Unexpected weight shape {weight.shape} for expected input {expected_in}")


def export_gpt2_static_bundle(
    model_name_or_path: str,
    output_path: Path,
    dtype: str = "float16",
) -> Path:
    """Export a GPT-2 style checkpoint as a static FNC bundle."""

    transformers = _ensure_transformers()
    torch_dtype = getattr(torch, dtype, torch.float16)
    model = transformers.AutoModelForCausalLM.from_pretrained(model_name_or_path, torch_dtype=torch_dtype)
    state = model.state_dict()
    cfg = FNCConfig()
    cfg.model.d_model = int(model.config.hidden_size)
    cfg.model.n_layers = int(model.config.n_layer)
    cfg.model.n_heads = int(model.config.num_attention_heads)
    cfg.model.vocab_size = int(model.config.vocab_size)
    cfg.model.max_seq_len = int(getattr(model.config, "max_position_embeddings", cfg.model.max_seq_len))
    n_inner = int(getattr(model.config, "n_inner", cfg.model.d_model * 4))
    cfg.model.mlp_ratio = max(1, n_inner // cfg.model.d_model)

    mlp_hidden = cfg.model.d_model * cfg.model.mlp_ratio
    weight_map: Dict[BlockSpec, torch.Tensor] = {}
    seeds = SeedRegistry(master_seed=0)

    for layer in range(cfg.model.n_layers):
        qkv_key = f"transformer.h.{layer}.attn.c_attn.weight"
        proj_key = f"transformer.h.{layer}.attn.c_proj.weight"
        fc1_key = f"transformer.h.{layer}.mlp.c_fc.weight"
        fc2_key = f"transformer.h.{layer}.mlp.c_proj.weight"

        qkv = _to_in_out(state[qkv_key].to(torch.float32), cfg.model.d_model)
        q, k, v = torch.split(qkv, cfg.model.d_model, dim=1)
        o = _to_in_out(state[proj_key].to(torch.float32), cfg.model.d_model)
        ff1 = _to_in_out(state[fc1_key].to(torch.float32), cfg.model.d_model)
        ff2 = _to_in_out(state[fc2_key].to(torch.float32), mlp_hidden)

        specs_and_weights = {
            ("attn_q_proj", layer, 0, cfg.model.d_model, cfg.model.d_model): q,
            ("attn_k_proj", layer, 0, cfg.model.d_model, cfg.model.d_model): k,
            ("attn_v_proj", layer, 0, cfg.model.d_model, cfg.model.d_model): v,
            ("attn_out_proj", layer, 0, cfg.model.d_model, cfg.model.d_model): o,
            ("mlp_fc1", layer, 0, cfg.model.d_model, mlp_hidden): ff1,
            ("mlp_fc2", layer, 0, mlp_hidden, cfg.model.d_model): ff2,
        }
        for spec, tensor in specs_and_weights.items():
            weight_map[spec] = tensor
            seeds.seed_for(spec)

    ln_weight = state.get("transformer.ln_f.weight")
    if ln_weight is not None:
        spec = ("ln_final", cfg.model.n_layers, 0, cfg.model.d_model, 1)
        weight_map[spec] = ln_weight.to(torch.float32).view(-1, 1)
        seeds.seed_for(spec)

    lm_head = _to_in_out(state["lm_head.weight"].to(torch.float32), cfg.model.d_model)
    lm_spec = ("lm_head", 0, 0, cfg.model.d_model, cfg.model.vocab_size)
    weight_map[lm_spec] = lm_head
    seeds.seed_for(lm_spec)

    static_generator = StaticWeightGenerator(weight_map)
    precision = PrecisionPolicy(default_bits=16)
    extras: Dict[str, object] = {
        "embedding": state["transformer.wte.weight"].to(torch.float32),
    }
    tokenizer_name: str | None = None
    try:  # pragma: no cover - optional dependency fetch
        tokenizer = transformers.AutoTokenizer.from_pretrained(model_name_or_path)
        tokenizer_name = tokenizer.name_or_path
    except Exception:  # pragma: no cover - best effort
        tokenizer_name = None
    if tokenizer_name:
        extras["tokenizer_name"] = tokenizer_name

    output_path = output_path if output_path.suffix else output_path.with_suffix(".pt")
    save_static_bundle(output_path, cfg, static_generator, seeds, precision, extras=extras)
    return output_path


__all__ = ["export_gpt2_static_bundle"]
