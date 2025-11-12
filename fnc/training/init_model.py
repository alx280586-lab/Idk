"""Utilities to instantiate untrained FNC bundles."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

try:  # pragma: no cover - optional dependency fallback
    from loguru import logger
except ImportError:  # pragma: no cover - fallback path for minimal environments
    import logging

    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

from fnc.fnc_core.config import FNCConfig
from fnc.fnc_core.model_stats import estimate_worker_params
from fnc.generator.checkpoints import save_generator_checkpoint
from fnc.training.pipeline import build_training_bundle


def initialise_model_bundle(
    cfg: FNCConfig,
    output_dir: Path,
    metadata: Optional[Dict[str, object]] = None,
) -> Path:
    """Create an untrained generator/worker bundle and persist it to disk."""

    bundle = build_training_bundle(cfg)
    bundle.generator.eval()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "generator.pt"
    footprint = estimate_worker_params(cfg)
    precision_state = bundle.precision.as_dict() if hasattr(bundle.precision, "as_dict") else {}
    seeds_state = bundle.seeds.as_dict()
    payload: Dict[str, object] = {
        "config": cfg.as_dict(),
        "model": bundle.generator.state_dict(),
        "precision": precision_state,
        "seeds": seeds_state,
        "metadata": {
            "bundle_type": "untrained_fnc",
            "status": "initialised",
            "num_lod": int(cfg.generator.num_lod),
            "footprint": footprint.as_dict(),
        },
    }
    if metadata:
        payload["metadata"].update(metadata)
    save_generator_checkpoint(target, payload)
    logger.info(
        "Initialised untrained bundle at %s (virtual params: %.2e)",
        target,
        footprint.virtual_params,
    )
    return target


__all__ = ["initialise_model_bundle"]
