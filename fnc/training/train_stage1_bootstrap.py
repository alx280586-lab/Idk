"""Stage 1 bootstrap training loop."""
from __future__ import annotations

from typing import Dict

from fnc.training.trainer_meta import meta_train_step


def run_stage1(dataloader, model_W, generator_G, optimizer, precision_ctrl, cfg) -> Dict[str, float]:
    """Run a single epoch of Stage 1 training."""
    metrics: Dict[str, float] = {}
    for batch in dataloader:
        metrics = meta_train_step(batch, model_W, generator_G, optimizer, precision_ctrl, cfg)
    return metrics


__all__ = ["run_stage1"]
