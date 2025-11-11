"""Stage 3 self-distillation scaffolding."""
from __future__ import annotations

from typing import Dict

import torch

from fnc.training.trainer_meta import meta_train_step


def run_stage3(dataloader, teacher_model, model_W, generator_G, optimizer, precision_ctrl, cfg) -> Dict[str, float]:
    """Run distillation by mixing teacher logits into the loss."""
    metrics: Dict[str, float] = {}
    alpha = cfg.training.distill_alpha
    for batch in dataloader:
        tokens, targets = batch
        with torch.no_grad():
            teacher_logits = teacher_model(tokens)
        logits = model_W(tokens)
        distill_loss = torch.nn.functional.mse_loss(logits, teacher_logits)
        lm_loss = torch.nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        loss = alpha * distill_loss + (1 - alpha) * lm_loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        metrics = {"loss": float(loss.item()), "lm_loss": float(lm_loss.item())}
    return metrics


__all__ = ["run_stage3"]
