"""Data pipeline stubs for meta-training."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import torch


class TextDataset:
    """Minimal text dataset that yields random token IDs."""

    def __init__(self, vocab_size: int, length: int = 1024, seed: int = 0) -> None:
        self.vocab_size = vocab_size
        g = torch.Generator().manual_seed(seed)
        self.data = torch.randint(0, vocab_size, (length,), generator=g)

    def __len__(self) -> int:
        return self.data.numel()

    def __getitem__(self, idx: int) -> int:
        return int(self.data[idx])


def create_dataloader(dataset: TextDataset, seq_len: int, batch_size: int) -> Iterable[Tuple[torch.Tensor, torch.Tensor]]:
    """Yield batches of token sequences and targets."""
    for start in range(0, len(dataset) - seq_len - 1, seq_len):
        tokens = torch.tensor(dataset.data[start : start + seq_len])
        targets = torch.tensor(dataset.data[start + 1 : start + seq_len + 1])
        yield tokens.view(1, -1).repeat(batch_size, 1), targets.view(1, -1).repeat(batch_size, 1)


__all__ = ["TextDataset", "create_dataloader"]
