"""ChatWeaver-4B model definition.

This module implements the transformer decoder-only architecture for the
ChatWeaver-4B model. The implementation is intentionally modular so that it can
be reused for pretraining, fine-tuning, and inference workloads.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class ChatWeaverConfig:
    """Configuration container for the ChatWeaver-4B model.

    The defaults follow the requirements outlined in the project brief but can
    be overridden via the YAML configuration file.
    """

    vocab_size: int = 50_000
    context_length: int = 4096
    hidden_size: int = 3072
    intermediate_size: int = 8192
    num_attention_heads: int = 32
    num_key_value_heads: int = 8
    num_layers: int = 36
    rotary_dim: Optional[int] = None
    layer_norm_eps: float = 1e-5
    dropout: float = 0.0
    activation_dropout: float = 0.0
    gradient_checkpointing: bool = True
    use_flash_attention: bool = True
    use_bias: bool = False
    initializer_range: float = 0.02

    def __post_init__(self) -> None:
        if self.hidden_size % self.num_attention_heads != 0:
            raise ValueError("hidden_size must be divisible by num_attention_heads")
        if self.num_attention_heads % self.num_key_value_heads != 0:
            raise ValueError("num_attention_heads must be divisible by num_key_value_heads")
        if self.rotary_dim is None:
            # Default to half of the head size for rotary embeddings.
            self.rotary_dim = self.hidden_size // self.num_attention_heads


class RotaryEmbedding(nn.Module):
    """Implements rotary positional embeddings.

    The implementation mirrors GPT-NeoX style rotary embeddings and supports the
    partial rotary dimension used for modern decoder models.
    """

    def __init__(self, dim: int, max_position_embeddings: int = 4096, base: int = 10_000) -> None:
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        t = torch.arange(max_position_embeddings, dtype=torch.float)
        freqs = torch.einsum("i,j->ij", t, inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos_cached", emb.cos(), persistent=False)
        self.register_buffer("sin_cached", emb.sin(), persistent=False)

    def forward(self, position_ids: torch.Tensor, dim: int) -> Tuple[torch.Tensor, torch.Tensor]:
        cos = self.cos_cached[position_ids][:, :, :dim].unsqueeze(1)
        sin = self.sin_cached[position_ids][:, :, :dim].unsqueeze(1)
        return cos, sin


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1, x2 = x[..., : x.shape[-1] // 2], x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
    rotary_dim: int,
) -> Tuple[torch.Tensor, torch.Tensor]:
    q_head, q_pass = q[..., :rotary_dim], q[..., rotary_dim:]
    k_head, k_pass = k[..., :rotary_dim], k[..., rotary_dim:]
    q_rot = (q_head * cos) + (rotate_half(q_head) * sin)
    k_rot = (k_head * cos) + (rotate_half(k_head) * sin)
    q = torch.cat((q_rot, q_pass), dim=-1)
    k = torch.cat((k_rot, k_pass), dim=-1)
    return q, k


class SwiGLU(nn.Module):
    """SwiGLU feed-forward block."""

    def __init__(self, hidden_size: int, intermediate_size: int, dropout: float) -> None:
        super().__init__()
        self.w1 = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.w2 = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.w3 = nn.Linear(intermediate_size, hidden_size, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x1 = self.w1(x)
        x2 = self.w2(x)
        x = F.silu(x1) * x2
        x = self.w3(x)
        return self.dropout(x)


class Attention(nn.Module):
    """Multi-head attention with grouped-query support."""

    def __init__(self, config: ChatWeaverConfig) -> None:
        super().__init__()
        self.num_heads = config.num_attention_heads
        self.num_key_value_heads = config.num_key_value_heads
        self.head_dim = config.hidden_size // config.num_attention_heads
        self.rotary_dim = min(config.rotary_dim or self.head_dim, self.head_dim)
        self.scale = self.head_dim ** -0.5

        self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=config.use_bias)
        self.k_proj = nn.Linear(config.hidden_size, self.num_key_value_heads * self.head_dim, bias=config.use_bias)
        self.v_proj = nn.Linear(config.hidden_size, self.num_key_value_heads * self.head_dim, bias=config.use_bias)
        self.o_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=config.use_bias)
        self.dropout = nn.Dropout(config.dropout)

        self.use_flash_attention = config.use_flash_attention

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor],
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]],
        position_cos: torch.Tensor,
        position_sin: torch.Tensor,
        use_cache: bool,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        bsz, seq_len, _ = hidden_states.size()

        query_states = self.q_proj(hidden_states)
        key_states = self.k_proj(hidden_states)
        value_states = self.v_proj(hidden_states)

        query_states = query_states.view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        key_states = key_states.view(bsz, seq_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        value_states = value_states.view(bsz, seq_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)

        query_states, key_states = apply_rotary_pos_emb(
            query_states, key_states, position_cos, position_sin, self.rotary_dim
        )

        if kv_cache is not None:
            past_key, past_value = kv_cache
            key_states = torch.cat([past_key, key_states], dim=2)
            value_states = torch.cat([past_value, value_states], dim=2)

        if use_cache:
            kv_cache = (key_states, value_states)
        else:
            kv_cache = None

        if self.num_key_value_heads != self.num_heads:
            # Expand key/value to match query heads via grouped-query attention.
            repeat_factor = self.num_heads // self.num_key_value_heads
            key_states = key_states.repeat_interleave(repeat_factor, dim=1)
            value_states = value_states.repeat_interleave(repeat_factor, dim=1)

        attn_output = self._scaled_dot_product_attention(
            query_states, key_states, value_states, attention_mask
        )
        attn_output = attn_output.transpose(1, 2).contiguous().view(bsz, seq_len, -1)
        attn_output = self.o_proj(attn_output)
        return attn_output, kv_cache

    def _scaled_dot_product_attention(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        attention_mask: Optional[torch.Tensor],
    ) -> torch.Tensor:
        if self.use_flash_attention and hasattr(F, "scaled_dot_product_attention"):
            attn_output = F.scaled_dot_product_attention(
                q, k, v, attn_mask=attention_mask, dropout_p=self.dropout.p if self.training else 0.0, is_causal=True
            )
        else:
            scores = torch.matmul(q, k.transpose(-1, -2)) * self.scale
            if attention_mask is not None:
                scores = scores + attention_mask
            scores = F.softmax(scores, dim=-1)
            scores = self.dropout(scores)
            attn_output = torch.matmul(scores, v)
        return attn_output


class DecoderLayer(nn.Module):
    """Single transformer decoder block."""

    def __init__(self, config: ChatWeaverConfig) -> None:
        super().__init__()
        self.input_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.attention = Attention(config)
        self.post_attention_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.mlp = SwiGLU(config.hidden_size, config.intermediate_size, config.activation_dropout)
        self.dropout = nn.Dropout(config.dropout)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor],
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]],
        position_cos: torch.Tensor,
        position_sin: torch.Tensor,
        use_cache: bool,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        attn_output, kv_cache = self.attention(
            hidden_states, attention_mask, kv_cache, position_cos, position_sin, use_cache
        )
        hidden_states = residual + self.dropout(attn_output)

        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = residual + self.dropout(self.mlp(hidden_states))
        return hidden_states, kv_cache


class ChatWeaverModel(nn.Module):
    """Decoder-only transformer language model for ChatWeaver-4B."""

    def __init__(self, config: ChatWeaverConfig) -> None:
        super().__init__()
        self.config = config
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.embed_dropout = nn.Dropout(config.dropout)
        self.layers = nn.ModuleList([DecoderLayer(config) for _ in range(config.num_layers)])
        self.norm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        self.rotary_emb = RotaryEmbedding(config.rotary_dim, max_position_embeddings=config.context_length)
        self.apply(self._init_weights)

        self.gradient_checkpointing = config.gradient_checkpointing

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        positions: Optional[torch.Tensor] = None,
        past_key_values: Optional[Iterable[Tuple[torch.Tensor, torch.Tensor]]] = None,
        use_cache: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        batch_size, seq_length = input_ids.size()
        if positions is None:
            position_ids = torch.arange(0, seq_length, device=input_ids.device)
            if past_key_values is not None:
                past_length = past_key_values[0][0].size(2)
                position_ids = position_ids + past_length
            position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        else:
            position_ids = positions
        cos, sin = self.rotary_emb(position_ids, self.config.rotary_dim)

        hidden_states = self.embed_tokens(input_ids)
        hidden_states = self.embed_dropout(hidden_states)

        if attention_mask is not None:
            attention_mask = self._prepare_attention_mask(attention_mask, hidden_states.dtype)

        next_kv = [] if use_cache else None
        all_hidden_states = [] if output_hidden_states else None

        for idx, layer in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states.append(hidden_states)

            layer_past = past_key_values[idx] if past_key_values is not None else None
            if self.gradient_checkpointing and self.training:
                def layer_forward(*inputs: torch.Tensor) -> torch.Tensor:
                    output, _ = layer(inputs[0], inputs[1], layer_past, cos, sin, use_cache)
                    return output

                hidden_states = torch.utils.checkpoint.checkpoint(
                    layer_forward, hidden_states, attention_mask, use_reentrant=False
                )
                layer_kv = None
                if use_cache:
                    _, layer_kv = layer(hidden_states, attention_mask, layer_past, cos, sin, use_cache)
            else:
                hidden_states, layer_kv = layer(
                    hidden_states, attention_mask, layer_past, cos, sin, use_cache
                )
            if use_cache:
                next_kv.append(layer_kv)

        hidden_states = self.norm(hidden_states)
        logits = self.lm_head(hidden_states)

        if output_hidden_states:
            all_hidden_states.append(hidden_states)

        return {
            "logits": logits,
            "past_key_values": tuple(next_kv) if use_cache else None,
            "hidden_states": tuple(all_hidden_states) if output_hidden_states else None,
        }

    @staticmethod
    def _prepare_attention_mask(attention_mask: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
        # Convert attention mask to additive form expected by flash attention fallback.
        inverted_mask = 1.0 - attention_mask[:, None, None, :]
        return inverted_mask.masked_fill(inverted_mask.bool(), torch.finfo(dtype).min)

    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int,
        temperature: float = 0.8,
        top_p: float = 0.95,
    ) -> torch.Tensor:
        """Greedy/nucleus sampling generation helper."""

        generated = input_ids
        past_key_values = None
        for _ in range(max_new_tokens):
            if past_key_values is None:
                model_inputs = generated[:, -self.config.context_length :]
            else:
                model_inputs = generated[:, -1:]
            outputs = self(
                model_inputs,
                past_key_values=past_key_values,
                use_cache=True,
            )
            logits = outputs["logits"][:, -1, :] / max(temperature, 1e-6)
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(self._top_p_filter(probs, top_p), num_samples=1)
            generated = torch.cat([generated, next_token], dim=-1)
            past_key_values = outputs["past_key_values"]
        return generated

    @staticmethod
    def _top_p_filter(probs: torch.Tensor, top_p: float) -> torch.Tensor:
        sorted_probs, sorted_indices = torch.sort(probs, descending=True)
        cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
        mask = cumulative_probs > top_p
        mask[..., 1:] = mask[..., :-1].clone()
        mask[..., 0] = False
        sorted_probs = sorted_probs.masked_fill(mask, 0.0)
        filtered_probs = torch.zeros_like(probs).scatter(-1, sorted_indices, sorted_probs)
        total = filtered_probs.sum(dim=-1, keepdim=True)
        filtered_probs = torch.where(total > 0, filtered_probs / total, probs)
        return filtered_probs

    def save_checkpoint(self, path: str, optimizer: Optional[torch.optim.Optimizer] = None) -> None:
        """Save model (and optimizer) state to disk."""
        state = {"model": self.state_dict(), "config": self.config.__dict__}
        if optimizer is not None:
            state["optimizer"] = optimizer.state_dict()
        torch.save(state, path)

    @classmethod
    def from_checkpoint(cls, path: str, map_location: Optional[str] = None) -> "ChatWeaverModel":
        """Load a model from a previously saved checkpoint."""
        checkpoint = torch.load(path, map_location=map_location)
        config = ChatWeaverConfig(**checkpoint["config"])
        model = cls(config)
        model.load_state_dict(checkpoint["model"])
        return model


def build_model(config_dict: Dict[str, Any]) -> ChatWeaverModel:
    """Factory helper to build a model from a dictionary."""

    config = ChatWeaverConfig(**config_dict)
    return ChatWeaverModel(config)


__all__ = ["ChatWeaverConfig", "ChatWeaverModel", "build_model"]
