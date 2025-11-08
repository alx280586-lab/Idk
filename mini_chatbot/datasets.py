"""Simple dialogue samples and dataset helpers for the reasoning chatbot."""

from typing import Iterable, List, Sequence, Tuple

import torch
from torch.utils.data import Dataset

from .tokenization import tokenize_chat_example

SAMPLE_DIALOGUES: List[Tuple[str, str]] = [
    ("USER: hi", "BOT: hey! how can i help you today?"),
    (
        "USER: what is 2+2?",
        "BOT: it's 4. THOUGHT: i added two and two to get four.",
    ),
    (
        "USER: tell me a joke",
        "BOT: THOUGHT: think of a computer joke. BOT: why did the byte go to therapy? because it couldn't process its feelings.",
    ),
    (
        "USER: explain why the sky looks blue",
        "BOT: THOUGHT: recall rayleigh scattering. BOT: sunlight scatters in the atmosphere and blue light spreads the most, so the sky looks blue to us.",
    ),
    (
        "USER: help me plan a study schedule",
        "BOT: THOUGHT: gather requirements then respond. BOT: let's break your goals into short daily sessions and review progress each week.",
    ),
]


class ReasoningChatDataset(Dataset):
    """Tokenizes USER/BOT chat pairs for teacher-forcing training."""

    def __init__(
        self, dialogues: Sequence[Tuple[str, str]], tokenizer, max_length: int
    ) -> None:
        self.examples: List[Tuple[torch.Tensor, torch.Tensor]] = []
        for user_text, bot_text in dialogues:
            input_ids, labels = tokenize_chat_example(
                tokenizer,
                user_text,
                bot_text,
                max_length=max_length,
            )
            self.examples.append((input_ids, labels))

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.examples[index]


def collate_batch(
    batch: Sequence[Tuple[torch.Tensor, torch.Tensor]],
    pad_token_id: int,
    device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Pad input/label tensors so everything in the batch has the same length."""

    input_tensors, label_tensors = zip(*batch)
    max_len = max(t.size(0) for t in input_tensors)

    padded_inputs = []
    padded_labels = []
    for input_ids, labels in batch:
        pad_len = max_len - input_ids.size(0)
        if pad_len > 0:
            pad_tensor = torch.full((pad_len,), pad_token_id, dtype=torch.long)
            input_ids = torch.cat([input_ids, pad_tensor], dim=0)
            labels = torch.cat([labels, torch.full_like(pad_tensor, -100)], dim=0)
        padded_inputs.append(input_ids)
        padded_labels.append(labels)

    input_batch = torch.stack(padded_inputs).to(device)
    label_batch = torch.stack(padded_labels).to(device)
    return input_batch, label_batch


def iter_batches(
    dataset: ReasoningChatDataset,
    batch_size: int,
    pad_token_id: int,
    device: torch.device,
) -> Iterable[Tuple[torch.Tensor, torch.Tensor]]:
    """Yield padded batches indefinitely to mimic a training loader."""

    batch: List[Tuple[torch.Tensor, torch.Tensor]] = []
    for example in dataset:
        batch.append(example)
        if len(batch) == batch_size:
            yield collate_batch(batch, pad_token_id, device)
            batch = []
    if batch:
        yield collate_batch(batch, pad_token_id, device)
