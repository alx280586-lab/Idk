"""Command-line text generation entry point."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import torch
import typer

from fnc.fnc_core.config import FNCConfig
from fnc.fnc_core.seeds import SeedRegistry
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.caching import SimpleCache
from fnc.generator.generator_model import FractalGenerator
from fnc.worker.worker_skeleton import FNCWorker, WorkerConfig

app = typer.Typer(add_completion=False)


def _load_config(config_path: Path) -> FNCConfig:
    payload = json.loads(config_path.read_text()) if config_path.suffix == ".json" else {}
    return FNCConfig.from_dict(payload) if payload else FNCConfig()


@app.command()
def main(
    bundle: Path = typer.Argument(..., help="Path to the model bundle."),
    prompt: str = typer.Option("Hello", help="Prompt to condition on."),
    max_new_tokens: int = typer.Option(32, help="Number of tokens to generate."),
    config: Optional[Path] = typer.Option(None, help="Optional config override."),
) -> None:
    cfg = _load_config(config) if config else FNCConfig()
    generator = FractalGenerator(cfg.generator)
    worker_cfg = WorkerConfig(
        d_model=cfg.model.d_model,
        n_layers=cfg.model.n_layers,
        n_heads=cfg.model.n_heads,
        vocab_size=cfg.model.vocab_size,
        max_seq_len=cfg.model.max_seq_len,
    )
    cache = SimpleCache()
    precision = PrecisionPolicy(cfg.generator.quant_policy.get("default_bits", 8))
    seeds = SeedRegistry(cfg.training.seed)
    worker = FNCWorker(worker_cfg, generator, cache, precision, seeds)
    tokens = torch.randint(0, worker_cfg.vocab_size, (1, cfg.model.max_seq_len))
    logits = worker(tokens)
    typer.echo(f"Generated logits shape: {tuple(logits.shape)}")


if __name__ == "__main__":
    app()
