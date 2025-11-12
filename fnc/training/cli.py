"""Command-line interface for FNC training stages."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
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
from fnc.training.init_model import initialise_model_bundle
from fnc.training.pipeline import (
    build_training_bundle,
    run_distillation,
    run_progressive_training,
    run_stage1_training,
)

app = typer.Typer(add_completion=False)


def _load_config(path: Optional[Path]) -> FNCConfig:
    if path is None:
        return FNCConfig()
    return FNCConfig.from_file(path)


@app.command()
def stage1(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file to load."),
    steps: Optional[int] = typer.Option(None, help="Maximum number of optimisation steps."),
    epochs: Optional[int] = typer.Option(None, help="Number of epochs to run."),
    checkpoint_dir: Optional[Path] = typer.Option(None, help="Directory to save checkpoints."),
) -> None:
    cfg = _load_config(config)
    bundle = build_training_bundle(cfg)
    metrics = run_stage1_training(bundle, epochs=epochs, max_steps=steps, checkpoint_dir=checkpoint_dir)
    logger.info("Stage 1 complete: %s", metrics)


@app.command()
def progressive(
    config: Optional[Path] = typer.Option(None, help="Config file to load."),
    steps: Optional[int] = typer.Option(None, help="Maximum number of optimisation steps."),
    epochs: Optional[int] = typer.Option(None, help="Number of epochs to run."),
    checkpoint_dir: Optional[Path] = typer.Option(None, help="Directory to save checkpoints."),
) -> None:
    cfg = _load_config(config)
    bundle = build_training_bundle(cfg)
    metrics = run_progressive_training(bundle, epochs=epochs, max_steps=steps, checkpoint_dir=checkpoint_dir)
    logger.info("Progressive training complete: %s", metrics)


@app.command()
def distill(
    config: Optional[Path] = typer.Option(None, help="Config file to load."),
    steps: Optional[int] = typer.Option(None, help="Maximum number of optimisation steps."),
    epochs: Optional[int] = typer.Option(None, help="Number of epochs to run."),
    checkpoint_dir: Optional[Path] = typer.Option(None, help="Directory to save checkpoints."),
) -> None:
    cfg = _load_config(config)
    bundle = build_training_bundle(cfg)
    metrics = run_distillation(bundle, epochs=epochs, max_steps=steps, checkpoint_dir=checkpoint_dir)
    logger.info("Distillation complete: %s", metrics)


@app.command()
def estimate(
    config: Optional[Path] = typer.Option(None, help="Config file to load."),
    lod: Optional[int] = typer.Option(None, help="Override generator LoD when computing the virtual parameter count."),
) -> None:
    """Print the theoretical parameter footprint for the configured worker."""

    cfg = _load_config(config)
    if lod is not None:
        cfg.generator.num_lod = lod
    footprint = estimate_worker_params(cfg)
    typer.echo("=== Worker Footprint ===")
    typer.echo(f"Physical parameters : {footprint.total_params:,}")
    typer.echo(f"Virtual parameters  : {footprint.virtual_params:,}")
    typer.echo(f"Bytes per block     : {footprint.bytes_per_block:,.0f}")
    typer.echo(f"Cache working set   : {footprint.cache_bytes:,.0f}")


@app.command()
def init(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file to load."),
    output: Path = typer.Option(Path("bundles/untrained"), help="Directory where the untrained bundle will be stored."),
) -> None:
    """Initialise an untrained FNC bundle without running optimisation."""

    cfg = _load_config(config)
    checkpoint_path = initialise_model_bundle(cfg, output)
    typer.echo(f"Initialised bundle saved to {checkpoint_path}")


if __name__ == "__main__":  # pragma: no cover
    app()
