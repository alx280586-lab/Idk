"""High-level training helper for ChatWeaver-4B.

This script bundles the most common setup steps so that non-experts can
bootstrap an experiment without manually editing YAML files.  It will:

1. Train a SentencePiece tokenizer from the provided corpora.
2. Populate sensible model/training defaults for the chosen scale preset.
3. Launch the standard training loop from :mod:`train`.

Run ``python quickstart.py --doctor`` first if you want to verify PyTorch and
SentencePiece are installed before kicking off a job.

The defaults target small-scale hardware (single consumer GPU or CPU demo),
but you can override batch sizes, precision, and the number of training steps
through CLI flags.  See ``TRAINING_GUIDE.md`` for a more comprehensive guide.
"""
from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Sequence

try:
    import sentencepiece as spm
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "SentencePiece is required for the quickstart workflow.\n"
        "Install the dependencies with:\n"
        "  pip install -r requirements.txt"
    ) from exc

from tokenizer_train import iter_corpus, write_sentencepiece_input

if TYPE_CHECKING:  # pragma: no cover - import-time type hints only
    from model import ChatWeaverConfig
    from train import OptimizerConfig, SchedulerConfig, TrainingConfig
    from train import run_training as RunTrainingFn

MODEL_PRESETS: Dict[str, Dict[str, int | float | bool]] = {
    "mini": {
        "hidden_size": 1024,
        "intermediate_size": 2730,
        "num_attention_heads": 8,
        "num_key_value_heads": 4,
        "num_layers": 12,
        "context_length": 1024,
        "use_flash_attention": False,
        "gradient_checkpointing": False,
    },
    "base": {
        "hidden_size": 2048,
        "intermediate_size": 5504,
        "num_attention_heads": 16,
        "num_key_value_heads": 8,
        "num_layers": 24,
        "context_length": 2048,
    },
    "full": {
        "hidden_size": 3072,
        "intermediate_size": 8192,
        "num_attention_heads": 32,
        "num_key_value_heads": 8,
        "num_layers": 36,
        "context_length": 4096,
    },
}


def ensure_paths(paths: Sequence[str]) -> Sequence[Path]:
    resolved = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            raise FileNotFoundError(f"Corpus path not found: {path}")
        resolved.append(path)
    return resolved


def run_doctor() -> None:
    """Inspect the local Python environment and print actionable guidance."""

    print("=== ChatWeaver Quickstart Doctor ===")
    print(f"Python: {platform.python_version()} ({platform.platform()})")

    missing = False

    try:
        import torch  # type: ignore

        print(f"✔ PyTorch {torch.__version__} detected")
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"  CUDA available: {device_name}")
        else:
            print("  CUDA not detected — training will run on CPU unless you install GPU drivers/wheels.")
    except ImportError:
        missing = True
        print("✖ PyTorch is missing. Install it with one of:")
        print("    pip install -r requirements.txt")
        print("    pip install torch --index-url https://download.pytorch.org/whl/cpu  # CPU build")
        print("    pip install torch --index-url https://download.pytorch.org/whl/cu121  # CUDA 12.1 build")

    try:
        import sentencepiece  # type: ignore

        print(f"✔ SentencePiece {sentencepiece.__version__} detected")
    except ImportError:
        missing = True
        print("✖ SentencePiece is missing. Install it with: pip install sentencepiece")

    if missing:
        raise SystemExit(1)


def train_quickstart_tokenizer(
    corpus_paths: Sequence[Path], work_dir: Path, vocab_size: int, jsonl_text_field: str | None
) -> Path:
    """Train a SentencePiece tokenizer for the quickstart workflow."""

    work_dir.mkdir(parents=True, exist_ok=True)
    tmp_file = work_dir / "quickstart_spm_input.txt"
    write_sentencepiece_input(iter_corpus(corpus_paths, jsonl_text_field), tmp_file)

    model_prefix = work_dir / "chatweaver_quickstart"
    spm.SentencePieceTrainer.Train(
        input=str(tmp_file),
        model_prefix=str(model_prefix),
        vocab_size=vocab_size,
        model_type="bpe",
        character_coverage=0.9995,
        num_threads=8,
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        byte_fallback=True,
        user_defined_symbols=["<|system|>", "<|user|>", "<|assistant|>"],
    )
    tmp_file.unlink(missing_ok=True)
    return Path(f"{model_prefix}.model")


def build_model_config(
    preset: str,
    vocab_size: int,
    context_length: int | None,
    config_cls: type["ChatWeaverConfig"],
) -> "ChatWeaverConfig":
    preset_values = MODEL_PRESETS[preset].copy()
    if context_length is not None:
        preset_values["context_length"] = context_length
    preset_values["vocab_size"] = vocab_size
    return config_cls(**preset_values)  # type: ignore[arg-type]


def build_training_config(
    train_files: Sequence[str],
    tokenizer_path: Path,
    output_dir: Path,
    args: argparse.Namespace,
) -> "TrainingConfig":
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_files = args.val_data if args.val_data else None
    from train import TrainingConfig  # Local import to delay PyTorch dependency

    cfg = TrainingConfig(
        train_data=list(train_files),
        eval_data=list(eval_files) if eval_files else None,
        tokenizer_path=str(tokenizer_path),
        output_dir=str(output_dir / "checkpoints"),
        batch_size=args.batch_size,
        micro_batch_size=args.micro_batch_size,
        max_steps=args.max_steps,
        save_interval=args.save_interval,
        eval_interval=args.eval_interval,
        log_interval=args.log_interval,
        precision=args.precision,
        seed=args.seed,
        resume_from=args.resume_from,
    )
    if args.lora_rank:
        cfg.lora = {
            "r": args.lora_rank,
            "alpha": args.lora_alpha,
            "dropout": args.lora_dropout,
        }
    return cfg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guided training launcher for ChatWeaver-4B")
    parser.add_argument(
        "--data",
        nargs="+",
        default=["examples/sample_dialog.jsonl"],
        help="One or more corpus files (text or JSONL).  Defaults to the bundled sample dataset.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run environment checks and exit without starting training.",
    )
    parser.add_argument(
        "--val-data",
        nargs="*",
        help="Optional evaluation corpus files.  Leave unset to skip evaluation.",
    )
    parser.add_argument(
        "--output-dir",
        default="quickstart_runs",
        help="Directory for tokenizer artifacts, checkpoints, and logs.",
    )
    parser.add_argument(
        "--vocab-size",
        type=int,
        default=32_000,
        help="Vocabulary size for the tokenizer.",
    )
    parser.add_argument(
        "--jsonl-text-field",
        default=None,
        help="Field name to read from JSONL corpora.  Use None to join all values.",
    )
    parser.add_argument(
        "--model-preset",
        choices=sorted(MODEL_PRESETS),
        default="mini",
        help="Model size preset.  'mini' runs comfortably on CPU/GPU for testing; 'full' is the 4B spec.",
    )
    parser.add_argument(
        "--context-length",
        type=int,
        default=None,
        help="Override context length.  Defaults to the preset value.",
    )
    parser.add_argument("--batch-size", type=int, default=8, help="Global batch size (across devices).")
    parser.add_argument(
        "--micro-batch-size",
        type=int,
        default=1,
        help="Per-device micro batch size.  Gradient accumulation is derived automatically.",
    )
    parser.add_argument("--max-steps", type=int, default=200, help="Number of optimizer steps to run.")
    parser.add_argument("--save-interval", type=int, default=50, help="Save checkpoints every N steps.")
    parser.add_argument("--eval-interval", type=int, default=50, help="Evaluate every N steps.")
    parser.add_argument("--log-interval", type=int, default=10, help="Log training metrics every N steps.")
    parser.add_argument(
        "--precision",
        choices=["fp32", "fp16", "bf16"],
        default="bf16",
        help="Numerical precision for the training loop.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--resume-from", default=None, help="Optional checkpoint path to resume training.")
    parser.add_argument(
        "--lora-rank",
        type=int,
        default=None,
        help="Enable LoRA fine-tuning with the specified rank.  Leave unset for full fine-tuning.",
    )
    parser.add_argument("--lora-alpha", type=float, default=32.0, help="LoRA scaling parameter (alpha).")
    parser.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout probability.")
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Optimizer learning rate.",
    )
    parser.add_argument(
        "--weight-decay",
        type=float,
        default=0.1,
        help="Optimizer weight decay.",
    )
    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=100,
        help="Linear warmup steps for the cosine scheduler.",
    )
    parser.add_argument(
        "--min-lr-ratio",
        type=float,
        default=0.1,
        help="Minimum learning-rate ratio for cosine annealing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.doctor:
        run_doctor()
        return

    from model import ChatWeaverConfig
    from train import OptimizerConfig, SchedulerConfig, run_training

    corpus_paths = ensure_paths(args.data)
    if args.val_data:
        ensure_paths(args.val_data)

    output_dir = Path(args.output_dir)
    tokenizer_dir = output_dir / "tokenizer"
    tokenizer_path = train_quickstart_tokenizer(
        corpus_paths, tokenizer_dir, args.vocab_size, args.jsonl_text_field
    )

    vocab_size = spm.SentencePieceProcessor(model_file=str(tokenizer_path)).vocab_size()
    model_cfg = build_model_config(args.model_preset, vocab_size, args.context_length, ChatWeaverConfig)

    train_cfg = build_training_config(args.data, tokenizer_path, output_dir, args)

    optim_cfg = OptimizerConfig(lr=args.learning_rate, weight_decay=args.weight_decay)
    sched_cfg = SchedulerConfig(
        warmup_steps=args.warmup_steps,
        total_steps=args.max_steps,
        min_lr_ratio=args.min_lr_ratio,
    )

    print("=== ChatWeaver Quickstart ===")
    print(json.dumps(
        {
            "model_config": asdict(model_cfg),
            "train_config": {
                k: v
                for k, v in asdict(train_cfg).items()
                if k not in {"train_data", "eval_data", "tokenizer_path"}
            },
            "tokenizer": str(tokenizer_path),
            "train_data": args.data,
            "eval_data": args.val_data or [],
        },
        indent=2,
    ))

    run_training(model_cfg, train_cfg, optim_cfg, sched_cfg)


if __name__ == "__main__":
    main()
