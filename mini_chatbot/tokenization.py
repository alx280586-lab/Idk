"""Tokenizer helpers for the reasoning chatbot demo."""

from typing import Tuple

import torch
from transformers import GPT2Tokenizer

SPECIAL_TOKENS = {
    "additional_special_tokens": ["USER:", "BOT:", "THOUGHT:", "<PAD>"]
}


def load_tokenizer(model_name: str = "gpt2") -> GPT2Tokenizer:
    """Load GPT-2 tokenizer and extend it with chat-specific tokens."""

    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    tokenizer.add_special_tokens(SPECIAL_TOKENS)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = "<PAD>"
    tokenizer.padding_side = "left"
    return tokenizer


def format_dialogue(user_text: str, bot_text: str) -> str:
    """Construct a prompt that encourages step-by-step reasoning."""

    return (
        f"{user_text.strip()}\n"
        "THOUGHT: let's think through the answer carefully.\n"
        f"{bot_text.strip()}"
    )


def tokenize_chat_example(
    tokenizer: GPT2Tokenizer, user_text: str, bot_text: str, max_length: int
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Tokenize a USER/BOT pair and return (input_ids, labels)."""

    prompt = format_dialogue(user_text, bot_text)
    encoded = tokenizer(
        prompt,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    input_ids = encoded["input_ids"].squeeze(0)
    labels = input_ids.clone()
    return input_ids, labels
