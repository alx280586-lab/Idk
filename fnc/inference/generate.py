"""Command-line text generation entry point."""
from __future__ import annotations

from pathlib import Path
from pathlib import Path
from time import perf_counter
from typing import Optional

import torch
import typer

from fnc.fnc_core.caching import SimpleCache
from fnc.fnc_core.config import FNCConfig
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry
from fnc.generator.checkpoints import load_generator_checkpoint
from fnc.generator.generator_model import FractalGenerator
from fnc.inference.static_generator import load_static_bundle
from fnc.training.data import ByteTokenizer
from fnc.worker.worker_skeleton import FNCWorker, WorkerConfig

app = typer.Typer(add_completion=False)


def _load_config(config_path: Optional[Path]) -> Optional[FNCConfig]:
    if config_path is None:
        return None
    if config_path.suffix in {".yaml", ".yml", ".json"}:
        return FNCConfig.from_file(config_path) if config_path.suffix != ".json" else FNCConfig.from_dict(__import__("json").loads(config_path.read_text()))
    raise ValueError(f"Unsupported config format: {config_path}")


def _restore_from_bundle(bundle: Path, cfg_override: Optional[FNCConfig]) -> tuple[FNCConfig, FractalGenerator, SeedRegistry, PrecisionPolicy]:
    ckpt_path = bundle / "generator.pt" if bundle.is_dir() else bundle
    state = load_generator_checkpoint(ckpt_path)
    if cfg_override is not None:
        cfg = cfg_override
    elif "config" in state:
        cfg = FNCConfig.from_dict(state["config"])
    else:
        cfg = FNCConfig()
    generator = FractalGenerator(cfg.generator)
    generator.load_state_dict(state.get("model", {}))
    precision_state = state.get("precision", {})
    precision = PrecisionPolicy(
        default_bits=precision_state.get("default_bits", cfg.generator.quant_policy.get("default_bits", 8)),
        overrides=precision_state.get("overrides"),
    )
    seeds = SeedRegistry(cfg.training.seed)
    if "seeds" in state:
        seeds.load_state(state["seeds"])
    return cfg, generator, seeds, precision


def _autoregressive_generate(worker: FNCWorker, tokenizer: ByteTokenizer, prompt: str, max_new_tokens: int) -> str:
    worker.eval()
    device = next(worker.parameters()).device
    prompt_tokens = tokenizer.encode(prompt)
    if prompt_tokens.numel() == 0:
        prompt_tokens = torch.zeros(1, dtype=torch.long)
    tokens = prompt_tokens.unsqueeze(0).to(device)
    generated = tokens.clone()
    for _ in range(max_new_tokens):
        window = generated[:, -worker.cfg.max_seq_len :]
        logits = worker(window)
        next_logits = logits[:, -1, :]
        probs = torch.softmax(next_logits, dim=-1)
        next_token = probs.argmax(dim=-1, keepdim=True)
        generated = torch.cat([generated, next_token], dim=1)
    return tokenizer.decode(generated[0].tolist())


@app.command()
def main(
    bundle: Path = typer.Argument(..., help="Path to the model bundle directory or generator checkpoint."),
    prompt: str = typer.Option("Fractal compression", help="Prompt to condition on."),
    max_new_tokens: int = typer.Option(32, help="Number of tokens to generate."),
    config: Optional[Path] = typer.Option(None, help="Optional config override."),
) -> None:
    cfg_override = _load_config(config)
    cfg, generator, seeds, precision = _restore_from_bundle(bundle, cfg_override)
    tokenizer = ByteTokenizer(vocab_size=cfg.model.vocab_size)
    worker_cfg = WorkerConfig(
        d_model=cfg.model.d_model,
        n_layers=cfg.model.n_layers,
        n_heads=cfg.model.n_heads,
        vocab_size=cfg.model.vocab_size,
        max_seq_len=cfg.model.max_seq_len,
        mlp_ratio=cfg.model.mlp_ratio,
    )
    cache = SimpleCache(max_entries=max(8, cfg.runtime.prefetch_window * 4))
    worker = FNCWorker(worker_cfg, generator, cache, precision, seeds)
    start = perf_counter()
    output_text = _autoregressive_generate(worker, tokenizer, prompt, max_new_tokens)
    duration = perf_counter() - start
    stats = cache.info()
    typer.echo(f"Output: {output_text}")
    typer.echo(f"Cache hits: {int(stats['hits'])}, misses: {int(stats['misses'])}, hit_rate: {stats['hit_rate']:.2f}")
    typer.echo(f"Latency: {duration*1000:.2f} ms for {max_new_tokens} tokens")


@app.command("static")
def generate_static(
    bundle: Path = typer.Argument(..., help="Path to a static bundle exported from Hugging Face."),
    prompt: str = typer.Option("Hello", help="Prompt to condition on."),
    max_new_tokens: int = typer.Option(32, help="Number of tokens to generate."),
    tokenizer_override: Optional[str] = typer.Option(
        None, help="Optional Hugging Face tokenizer name to override bundle metadata."
    ),
) -> None:
    cfg, generator, seeds, precision, extras = load_static_bundle(bundle)
    cache = SimpleCache(max_entries=max(8, cfg.runtime.prefetch_window * 4))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    worker_cfg = WorkerConfig(
        d_model=cfg.model.d_model,
        n_layers=cfg.model.n_layers,
        n_heads=cfg.model.n_heads,
        vocab_size=cfg.model.vocab_size,
        max_seq_len=cfg.model.max_seq_len,
        mlp_ratio=cfg.model.mlp_ratio,
    )
    worker = FNCWorker(worker_cfg, generator, cache, precision, seeds).to(device)
    embedding = extras.get("embedding")
    if isinstance(embedding, torch.Tensor):
        with torch.no_grad():
            target = worker.embed_tokens.weight.data
            rows = min(target.shape[0], embedding.shape[0])
            cols = min(target.shape[1], embedding.shape[1])
            target[:rows, :cols] = embedding[:rows, :cols]
    tokenizer_name = tokenizer_override or (extras.get("tokenizer_name") if isinstance(extras.get("tokenizer_name"), str) else None)
    hf_tokenizer = None
    if tokenizer_name:
        try:  # pragma: no cover - optional dependency
            from transformers import AutoTokenizer  # type: ignore

            hf_tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        except Exception as exc:  # pragma: no cover - optional dependency
            typer.echo(f"Warning: failed to load tokenizer '{tokenizer_name}': {exc}")
            hf_tokenizer = None
    if hf_tokenizer:
        encoded = hf_tokenizer.encode(prompt, add_special_tokens=False)
        if not encoded:
            bos = getattr(hf_tokenizer, "bos_token_id", None)
            encoded = [bos] if bos is not None else [0]
        tokens = torch.tensor(encoded, dtype=torch.long).unsqueeze(0)

        def decode_fn(ids: list[int]) -> str:
            return hf_tokenizer.decode(ids, skip_special_tokens=True)

    else:
        tokenizer = ByteTokenizer(vocab_size=cfg.model.vocab_size)
        encoded = tokenizer.encode(prompt)
        if encoded.numel() == 0:
            encoded = torch.zeros(1, dtype=torch.long)
        tokens = encoded.unsqueeze(0)

        def decode_fn(ids: list[int]) -> str:
            return tokenizer.decode(ids)

    tokens = tokens[:, -worker.cfg.max_seq_len :].to(device)
    generated = tokens.clone()
    start = perf_counter()
    for _ in range(max_new_tokens):
        window = generated[:, -worker.cfg.max_seq_len :]
        logits = worker(window)
        next_logits = logits[:, -1, :]
        next_token = next_logits.argmax(dim=-1, keepdim=True)
        generated = torch.cat([generated, next_token], dim=1)
    duration = perf_counter() - start
    output_tokens = [int(t) for t in generated[0].tolist()]
    typer.echo(f"Output: {decode_fn(output_tokens)}")
    stats = cache.info()
    typer.echo(
        f"Cache hits: {int(stats['hits'])}, misses: {int(stats['misses'])}, hit_rate: {stats['hit_rate']:.2f}"
    )
    typer.echo(f"Latency: {duration*1000:.2f} ms for {max_new_tokens} tokens")


if __name__ == "__main__":  # pragma: no cover
    app()
