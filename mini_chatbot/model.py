"""High-level model definition for the reasoning-focused mini GPT chatbot."""

from typing import Optional

import torch
import torch.nn as nn

from .config import ChatbotConfig
from .model_components import TransformerBlock


class MiniReasoningGPT(nn.Module):
    """A compact GPT-style decoder with rotary attention and gated MLPs."""

    def __init__(self, config: ChatbotConfig) -> None:
        super().__init__()
        self.config = config
        self.token_embeddings = nn.Embedding(config.vocab_size, config.hidden_size)
        self.position_embeddings = nn.Embedding(config.max_seq_len, config.hidden_size)
        self.dropout = nn.Dropout(config.dropout)

        self.blocks = nn.ModuleList([TransformerBlock(config) for _ in range(config.num_layers)])
        self.final_norm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_epsilon)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        self.token_embeddings.weight = self.lm_head.weight

    def forward(
        self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)

        positions = torch.arange(0, input_ids.size(1), device=input_ids.device)
        positions = positions.unsqueeze(0).expand_as(input_ids)

        token_emb = self.token_embeddings(input_ids)
        pos_emb = self.position_embeddings(positions)
        hidden_states = self.dropout(token_emb + pos_emb)

        for block in self.blocks:
            hidden_states = block(hidden_states)

        hidden_states = self.final_norm(hidden_states)
        logits = self.lm_head(hidden_states)
        return logits


def build_model(config: ChatbotConfig) -> MiniReasoningGPT:
    """Factory helper that moves the model to the configured device."""

    model = MiniReasoningGPT(config)
    return model.to(torch.device(config.device))
