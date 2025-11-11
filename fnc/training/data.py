"""Data pipeline utilities for meta-training."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import torch


class ByteTokenizer:
    """A tiny tokenizer that operates on raw bytes."""

    def __init__(self, vocab_size: int = 256) -> None:
        if vocab_size < 256:
            raise ValueError("vocab_size must be >= 256 for byte-level tokenisation")
        self.vocab_size = vocab_size

    def encode(self, text: str) -> torch.Tensor:
        data = [ord(ch) % 256 for ch in text]
        if not data:
            return torch.zeros(0, dtype=torch.long)
        return torch.tensor(data, dtype=torch.long)

    def decode(self, tokens: Sequence[int]) -> str:
        return "".join(chr(int(token) % 256) for token in tokens)


class TextDataset:
    """Text dataset backed by an in-memory tensor of token IDs."""

    def __init__(
        self,
        vocab_size: int,
        length: int = 1024,
        seed: int = 0,
        tokens: Optional[torch.Tensor] = None,
    ) -> None:
        self.vocab_size = vocab_size
        if tokens is not None:
            self.data = tokens.long()
        else:
            g = torch.Generator().manual_seed(seed)
            self.data = torch.randint(0, vocab_size, (length,), generator=g)
        self.seed = seed

    @classmethod
    def from_text(cls, text: str, tokenizer: Optional[ByteTokenizer] = None, seed: int = 0) -> "TextDataset":
        tokenizer = tokenizer or ByteTokenizer()
        tokens = tokenizer.encode(text)
        vocab_size = max(tokenizer.vocab_size, int(tokens.max().item()) + 1 if tokens.numel() else tokenizer.vocab_size)
        return cls(vocab_size=vocab_size, length=len(tokens), seed=seed, tokens=tokens)

    @classmethod
    def from_file(cls, path: Path, tokenizer: Optional[ByteTokenizer] = None, seed: int = 0) -> "TextDataset":
        text = path.read_text(encoding="utf-8")
        return cls.from_text(text, tokenizer=tokenizer, seed=seed)

    def __len__(self) -> int:
        return self.data.numel()

    def __getitem__(self, idx: int) -> int:
        return int(self.data[idx])


def create_dataloader(dataset: TextDataset, seq_len: int, batch_size: int) -> Iterable[Tuple[torch.Tensor, torch.Tensor]]:
    """Yield batches of token sequences and shifted targets."""

    tokens = dataset.data
    if tokens.numel() <= seq_len:
        repeat = (seq_len + 1) // max(1, tokens.numel()) + 1
        tokens = tokens.repeat(repeat)
    for start in range(0, tokens.numel() - seq_len - 1, seq_len):
        window = tokens[start : start + seq_len + 1]
        inputs = window[:-1].unsqueeze(0).repeat(batch_size, 1)
        targets = window[1:].unsqueeze(0).repeat(batch_size, 1)
        yield inputs, targets


__all__ = ["ByteTokenizer", "TextDataset", "create_dataloader"]
