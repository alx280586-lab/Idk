"""Tokenizer training utility for ChatWeaver-4B.

This script trains a SentencePiece tokenizer compatible with other modern LLMs.
It supports both plain-text and JSONL (Alpaca-style) datasets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import sentencepiece as spm


def iter_corpus(paths: Sequence[Path], jsonl_text_field: str | None = "text") -> Iterator[str]:
    """Yield text samples from the provided files."""

    for path in paths:
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as fp:
                for line in fp:
                    record = json.loads(line)
                    if jsonl_text_field is None:
                        yield " ".join(str(v) for v in record.values())
                    else:
                        value = record.get(jsonl_text_field)
                        if value is None:
                            continue
                        yield str(value)
        else:
            with path.open("r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if line:
                        yield line


def write_sentencepiece_input(samples: Iterable[str], output_file: Path) -> None:
    """Write a temporary file for SentencePiece training."""

    with output_file.open("w", encoding="utf-8") as fp:
        for sample in samples:
            fp.write(sample.replace("\n", " ") + "\n")


def train_tokenizer(args: argparse.Namespace) -> None:
    """Train and serialize a SentencePiece tokenizer."""

    corpus_paths = [Path(p) for p in args.corpus]
    tmp_file = Path(args.work_dir) / "spm_input.txt"
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    write_sentencepiece_input(iter_corpus(corpus_paths, args.jsonl_text_field), tmp_file)

    model_prefix = Path(args.work_dir) / args.model_prefix
    spm.SentencePieceTrainer.Train(
        input=str(tmp_file),
        model_prefix=str(model_prefix),
        vocab_size=args.vocab_size,
        model_type="bpe",
        character_coverage=args.character_coverage,
        num_threads=args.num_threads,
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        byte_fallback=True,
        user_defined_symbols=["<|system|>", "<|user|>", "<|assistant|>"]
    )

    if not args.keep_temp:
        tmp_file.unlink(missing_ok=True)

    print(f"Tokenizer artifacts written to {model_prefix}.*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a SentencePiece tokenizer for ChatWeaver-4B.")
    parser.add_argument("corpus", nargs="+", help="One or more corpus files (text or JSONL).")
    parser.add_argument("--work-dir", default="tokenizer", help="Directory for temporary and output files.")
    parser.add_argument("--model-prefix", default="chatweaver-spm", help="SentencePiece model prefix.")
    parser.add_argument("--vocab-size", type=int, default=50_000, help="Target vocabulary size.")
    parser.add_argument("--jsonl-text-field", default="text", help="Field name for JSONL entries.")
    parser.add_argument("--character-coverage", type=float, default=0.9995, help="Character coverage for SentencePiece.")
    parser.add_argument("--num-threads", type=int, default=8, help="Threads for SentencePiece training.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temporary preprocessed corpus file.")
    return parser.parse_args()


if __name__ == "__main__":
    train_tokenizer(parse_args())
