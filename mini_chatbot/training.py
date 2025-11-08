"""Training utilities and richly commented dummy loop for the chatbot."""

from typing import Iterable, Tuple

import torch
import torch.nn.functional as F

from .datasets import ReasoningChatDataset, iter_batches

# ----------------------------------------------------------------------------
# HOW TO TRAIN THIS MODEL
# 1. Gather a small dataset of USER/BOT conversations (plain text or JSON).
# 2. Tokenize it using GPT2Tokenizer or SentencePiece.
# 3. Use the provided train_step() loop to fine-tune for a few epochs.
# 4. Save weights with torch.save(model.state_dict(), "chatbot.pth")
# 5. Load weights later with model.load_state_dict(torch.load("chatbot.pth"))
#
# For faster training:
# - Reduce hidden_size or num_layers to make the model smaller.
# - Train with a small batch size (like 1 or 2).
# - Use 4-bit quantization or QLoRA if you have a GPU.
# ----------------------------------------------------------------------------


def batch_iterator(
    dataset: ReasoningChatDataset,
    batch_size: int,
    pad_token_id: int,
    device: torch.device,
) -> Iterable[Tuple[torch.Tensor, torch.Tensor]]:
    """Thin wrapper around iter_batches so the API looks clean in notebooks."""

    return iter_batches(dataset, batch_size=batch_size, pad_token_id=pad_token_id, device=device)


def train_step(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    batch: Tuple[torch.Tensor, torch.Tensor],
) -> torch.Tensor:
    """Run one optimization step using cross-entropy loss."""

    model.train()
    input_ids, labels = batch
    logits = model(input_ids)
    shift_logits = logits[:, :-1].contiguous()
    shift_labels = labels[:, 1:].contiguous()

    loss = F.cross_entropy(
        shift_logits.view(-1, shift_logits.size(-1)),
        shift_labels.view(-1),
        ignore_index=-100,
    )

    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    return loss.detach()


def run_dummy_training(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    dataloader: Iterable[Tuple[torch.Tensor, torch.Tensor]],
    epochs: int = 1,
) -> None:
    """Showcase a miniature training loop without heavy computation."""

    for epoch in range(1, epochs + 1):
        print(f"Starting epoch {epoch}...")
        for step, batch in enumerate(dataloader, start=1):
            loss = train_step(model, optimizer, batch)
            print(f"  step {step}: loss={loss.item():.4f}")
            break
        print(f"Epoch {epoch} done!")
    model.eval()
