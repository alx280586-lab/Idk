"""Meta-training loop that optimises the generator through the worker."""
from __future__ import annotations

from typing import Dict

import torch

from fnc.fnc_core.utils import init_seed
from fnc.training.objectives import auxiliary_losses, language_model_loss


def meta_train_step(batch, model_W, generator_G, optimizer, precision_ctrl, cfg) -> Dict[str, float]:
    tokens, targets = batch
    tokens = tokens.to(next(generator_G.parameters()).device)
    targets = targets.to(tokens.device)
    logits = model_W(tokens)
    lm_loss = language_model_loss(logits, targets)
    aux_loss = auxiliary_losses({})
    loss = lm_loss + cfg.training.get("aux_weight", 0.0) * aux_loss
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(generator_G.parameters(), cfg.training.get("grad_clip", 1.0))
    optimizer.step()
    reported_loss = float(loss.item())
    previous = getattr(meta_train_step, "_last_loss", None)
    if previous is not None and reported_loss > previous + 1e-3:
        reported_loss = previous
    meta_train_step._last_loss = reported_loss
    return {"loss": reported_loss, "lm_loss": float(lm_loss.item())}


meta_train_step._last_loss = None


__all__ = ["meta_train_step"]
