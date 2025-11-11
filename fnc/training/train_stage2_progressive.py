"""Progressive detail unlocking for Stage 2."""
from __future__ import annotations

from typing import Dict


def maybe_unlock_next_lod(step: int, generator_G, cfg) -> bool:
    """Increase generator LoD based on milestones."""
    milestones = cfg.training.get("lod_milestones", [])
    if step in milestones and generator_G.num_lod < cfg.generator.num_lod:
        generator_G.num_lod += 1
        return True
    return False


def run_stage2(dataloader, model_W, generator_G, optimizer, precision_ctrl, cfg) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    for step, batch in enumerate(dataloader):
        maybe_unlock_next_lod(step, generator_G, cfg)
        metrics = meta_train_step(batch, model_W, generator_G, optimizer, precision_ctrl, cfg)
    return metrics


from fnc.training.trainer_meta import meta_train_step


__all__ = ["maybe_unlock_next_lod", "run_stage2"]
