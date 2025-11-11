"""Command-line interface for FNC training stages."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from fnc.fnc_core.config import FNCConfig
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


if __name__ == "__main__":  # pragma: no cover
    app()
