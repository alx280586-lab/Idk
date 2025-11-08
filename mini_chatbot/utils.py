"""Utility helpers for displaying configuration and parameter counts."""

from typing import Iterable

import torch

from .config import ChatbotConfig


def count_parameters(model: torch.nn.Module) -> int:
    """Return the total number of trainable parameters."""

    return sum(param.numel() for param in model.parameters() if param.requires_grad)


def describe_model(model: torch.nn.Module, config: ChatbotConfig) -> None:
    """Pretty-print the configuration and parameter count for beginners."""

    print("Model configuration summary:")
    for key, value in config.summary_rows():
        print(f"  - {key}: {value}")

    total_params = count_parameters(model)
    print(f"Total parameters: {total_params:,}")
    if total_params > 1_000_000_000:
        print("This configuration is very large. Consider reducing hidden_size or num_layers.")
    elif total_params > 100_000_000:
        print("This configuration might need a strong GPU. For laptops, try hidden_size <= 512.")
    else:
        print("This configuration is small enough for CPU experimentation.")


def chunk_tensor(tensor: torch.Tensor, size: int) -> Iterable[torch.Tensor]:
    """Yield smaller pieces of a tensor to inspect values without printing everything."""

    for start in range(0, tensor.size(0), size):
        yield tensor[start : start + size]
