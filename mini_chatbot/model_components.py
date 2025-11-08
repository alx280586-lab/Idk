"""Core neural network building blocks for the reasoning chatbot."""

import math
from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import ChatbotConfig


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Helper used for rotary position embeddings."""

    x1 = x[..., ::2]
    x2 = x[..., 1::2]
    return torch.stack((-x2, x1), dim=-1).reshape_as(x)


class RotaryEmbedding(nn.Module):
    """Computes rotary positional embeddings for attention heads."""

    def __init__(self, head_dim: int, max_position: int, base: float) -> None:
        super().__init__()
        if head_dim % 2 != 0:
            raise ValueError("Rotary embeddings require an even head dimension.")
        inv_freq = 1.0 / (base ** (torch.arange(0, head_dim, 2).float() / head_dim))
        self.register_buffer("inv_freq", inv_freq)
        self.max_position = max_position

    def _get_embed(self, seq_len: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        positions = torch.arange(seq_len, device=device).type_as(self.inv_freq)
        freqs = torch.einsum("i , j -> i j", positions, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos()[None, None, :, :], emb.sin()[None, None, :, :]

    def forward(
        self, q: torch.Tensor, k: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:  # shape: (batch, heads, seq, head_dim)
        seq_len = q.size(-2)
        cos, sin = self._get_embed(seq_len, q.device)
        q_rot = (q * cos) + (_rotate_half(q) * sin)
        k_rot = (k * cos) + (_rotate_half(k) * sin)
        return q_rot, k_rot


class CausalSelfAttention(nn.Module):
    """Multi-head self-attention with rotary embeddings and dropout."""

    def __init__(self, config: ChatbotConfig) -> None:
        super().__init__()
        self.num_heads = config.num_heads
        self.head_dim = config.hidden_size // config.num_heads
        self.scale = 1.0 / math.sqrt(self.head_dim)

        self.q_proj = nn.Linear(config.hidden_size, config.hidden_size)
        self.k_proj = nn.Linear(config.hidden_size, config.hidden_size)
        self.v_proj = nn.Linear(config.hidden_size, config.hidden_size)
        self.out_proj = nn.Linear(config.hidden_size, config.hidden_size)

        self.attn_dropout = nn.Dropout(config.attention_dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        self.rotary = RotaryEmbedding(self.head_dim, config.max_seq_len, config.rotary_base)

        mask = torch.full((config.max_seq_len, config.max_seq_len), float("-inf"))
        mask = torch.triu(mask, diagonal=1)
        self.register_buffer("causal_mask", mask, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.size()

        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)

        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        q, k = self.rotary(q, k)

        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        attn_scores = attn_scores + self.causal_mask[:seq_len, :seq_len]

        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.attn_dropout(attn_weights)

        context = torch.matmul(attn_weights, v)
        context = context.transpose(1, 2).contiguous().view(batch_size, seq_len, -1)

        output = self.out_proj(context)
        return self.resid_dropout(output)


class FeedForward(nn.Module):
    """Gated feed-forward block inspired by recent reasoning-focused GPTs."""

    def __init__(self, config: ChatbotConfig) -> None:
        super().__init__()
        inner_dim = int(config.hidden_size * config.ff_multiplier)
        self.w1 = nn.Linear(config.hidden_size, inner_dim)
        self.w2 = nn.Linear(inner_dim, config.hidden_size)
        self.w3 = nn.Linear(config.hidden_size, inner_dim)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        hidden = self.w1(x)
        gate = torch.sigmoid(self.w3(x))
        activated = F.silu(hidden) * gate
        return self.dropout(self.w2(activated))


class TransformerBlock(nn.Module):
    """Single decoder block with pre-norm layout."""

    def __init__(self, config: ChatbotConfig) -> None:
        super().__init__()
        self.ln_1 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_epsilon)
        self.attn = CausalSelfAttention(config)
        self.ln_2 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_epsilon)
        self.ff = FeedForward(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln_1(x))
        x = x + self.ff(self.ln_2(x))
        return x
