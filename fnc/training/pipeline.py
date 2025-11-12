"""High-level training orchestration utilities."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple

import torch
from loguru import logger

from fnc.fnc_core.caching import SimpleCache
from fnc.fnc_core.config import FNCConfig
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry
from fnc.fnc_core.utils import init_seed
from fnc.generator.checkpoints import save_generator_checkpoint
from fnc.generator.generator_model import FractalGenerator
from fnc.training.checkpointing import save_training_state
from fnc.training.data import ByteTokenizer, TextDataset, create_dataloader
from fnc.training.optimizer import build_optimizer
from fnc.training.trainer_meta import meta_train_step
from fnc.training.train_stage2_progressive import maybe_unlock_next_lod
from fnc.training.train_stage3_distill import run_stage3
from fnc.worker.worker_skeleton import FNCWorker, WorkerConfig


@dataclass
class TrainingBundle:
    """Container for all components required during training."""

    config: FNCConfig
    generator: FractalGenerator
    worker: FNCWorker
    cache: SimpleCache
    precision: PrecisionPolicy
    seeds: SeedRegistry
    tokenizer: ByteTokenizer
    dataset: TextDataset


def _resolve_dataset(cfg: FNCConfig) -> Tuple[TextDataset, ByteTokenizer]:
    tokenizer = ByteTokenizer(vocab_size=cfg.model.vocab_size)
    default_path = Path(__file__).resolve().parents[1] / "data" / "tiny_corpus.txt"
    dataset_path = Path(cfg.data.dataset_path) if cfg.data.dataset_path else default_path
    if dataset_path.exists():
        dataset = TextDataset.from_file(dataset_path, tokenizer=tokenizer, seed=cfg.training.seed)
    else:
        logger.warning("Dataset %s not found; falling back to synthetic data.", dataset_path)
        synth_length = max(cfg.model.max_seq_len * 32, 1024)
        dataset = TextDataset(vocab_size=cfg.model.vocab_size, length=synth_length, seed=cfg.training.seed)
    return dataset, tokenizer


def build_training_bundle(cfg: FNCConfig) -> TrainingBundle:
    """Initialise models, caches, and tokenisers for training runs."""

    init_seed(cfg.training.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = FractalGenerator(cfg.generator).to(device)
    precision = PrecisionPolicy(
        default_bits=cfg.generator.quant_policy.get("default_bits", 8),
        overrides=cfg.generator.quant_policy.get("overrides"),
    )
    cache = SimpleCache(
        max_entries=max(8, cfg.runtime.prefetch_window * 4),
        max_bytes=getattr(cfg.runtime, "cache_bytes_gpu", None),
    )
    seeds = SeedRegistry(cfg.training.seed)
    worker_cfg = WorkerConfig(
        d_model=cfg.model.d_model,
        n_layers=cfg.model.n_layers,
        n_heads=cfg.model.n_heads,
        vocab_size=cfg.model.vocab_size,
        max_seq_len=cfg.model.max_seq_len,
        mlp_ratio=cfg.model.mlp_ratio,
    )
    worker = FNCWorker(worker_cfg, generator, cache, precision, seeds).to(device)
    dataset, tokenizer = _resolve_dataset(cfg)
    logger.info("Training bundle ready on %s with vocab %d", device, dataset.vocab_size)
    return TrainingBundle(
        cfg=cfg,
        generator=generator,
        worker=worker,
        cache=cache,
        precision=precision,
        seeds=seeds,
        tokenizer=tokenizer,
        dataset=dataset,
    )


def _batch_iterator(dataset: TextDataset, cfg: FNCConfig) -> Iterator[Tuple[torch.Tensor, torch.Tensor]]:
    seq_len = cfg.model.max_seq_len
    batch_size = max(1, cfg.training.batch_tokens // seq_len)
    return create_dataloader(dataset, seq_len=seq_len, batch_size=batch_size)


def _log_metrics(step: int, metrics: Dict[str, float]) -> None:
    message = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
    logger.info("step %d: %s", step, message)


def run_stage1_training(bundle: TrainingBundle, epochs: Optional[int] = None, max_steps: Optional[int] = None, checkpoint_dir: Optional[Path] = None) -> Dict[str, float]:
    """Execute Stage 1 bootstrap training."""

    cfg = bundle.config
    optimizer = build_optimizer(bundle.generator.parameters(), cfg)
    bundle.generator.train()
    bundle.worker.train()
    final_metrics: Dict[str, float] = {}
    epochs = epochs or cfg.training.epochs
    step = 0
    for epoch in range(epochs):
        for batch in _batch_iterator(bundle.dataset, cfg):
            final_metrics = meta_train_step(batch, bundle.worker, bundle.generator, optimizer, bundle.precision, cfg)
            bundle.cache.clear()
            step += 1
            if step % 10 == 0:
                _log_metrics(step, final_metrics)
            if max_steps and step >= max_steps:
                break
        if max_steps and step >= max_steps:
            break
    if checkpoint_dir:
        _save_training_artifacts(bundle, checkpoint_dir, final_metrics, optimizer)
    return final_metrics


def run_progressive_training(bundle: TrainingBundle, epochs: Optional[int] = None, max_steps: Optional[int] = None, checkpoint_dir: Optional[Path] = None) -> Dict[str, float]:
    cfg = bundle.config
    optimizer = build_optimizer(bundle.generator.parameters(), cfg)
    bundle.generator.train()
    bundle.worker.train()
    metrics: Dict[str, float] = {}
    epochs = epochs or cfg.training.epochs
    step = 0
    for epoch in range(epochs):
        for batch in _batch_iterator(bundle.dataset, cfg):
            maybe_unlock_next_lod(step, bundle.generator, cfg)
            metrics = meta_train_step(batch, bundle.worker, bundle.generator, optimizer, bundle.precision, cfg)
            bundle.cache.clear()
            step += 1
            if step % 10 == 0:
                _log_metrics(step, metrics)
            if max_steps and step >= max_steps:
                break
        if max_steps and step >= max_steps:
            break
    if checkpoint_dir:
        _save_training_artifacts(bundle, checkpoint_dir, metrics, optimizer)
    return metrics


def run_distillation(bundle: TrainingBundle, teacher: Optional[FNCWorker] = None, epochs: Optional[int] = None, max_steps: Optional[int] = None, checkpoint_dir: Optional[Path] = None) -> Dict[str, float]:
    cfg = bundle.config
    optimizer = build_optimizer(bundle.generator.parameters(), cfg)
    bundle.generator.train()
    bundle.worker.train()
    teacher = teacher or bundle.worker
    metrics: Dict[str, float] = {}
    epochs = epochs or cfg.training.epochs
    step = 0
    for epoch in range(epochs):
        for batch in _batch_iterator(bundle.dataset, cfg):
            metrics = run_stage3([batch], teacher, bundle.worker, bundle.generator, optimizer, bundle.precision, cfg)
            bundle.cache.clear()
            step += 1
            if step % 10 == 0:
                _log_metrics(step, metrics)
            if max_steps and step >= max_steps:
                break
        if max_steps and step >= max_steps:
            break
    if checkpoint_dir:
        _save_training_artifacts(bundle, checkpoint_dir, metrics, optimizer)
    return metrics


def _save_training_artifacts(bundle: TrainingBundle, checkpoint_dir: Path, metrics: Dict[str, float], optimizer: torch.optim.Optimizer) -> None:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    generator_state = {
        "model": bundle.generator.state_dict(),
        "config": bundle.config.as_dict(),
        "seeds": bundle.seeds.as_dict(),
        "precision": {
            "default_bits": bundle.precision.default_bits,
            "overrides": bundle.precision.overrides or {},
        },
        "metrics": metrics,
    }
    save_generator_checkpoint(checkpoint_dir / "generator.pt", generator_state)
    save_training_state(
        checkpoint_dir / "optimizer.pt",
        {
            "optimizer": optimizer.state_dict(),
            "metrics": metrics,
        },
    )
    logger.info("Saved training artefacts to %s", checkpoint_dir)


__all__ = [
    "TrainingBundle",
    "build_training_bundle",
    "run_stage1_training",
    "run_progressive_training",
    "run_distillation",
]
