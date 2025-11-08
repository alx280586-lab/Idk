"""Training entrypoint for ChatWeaver-4B."""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import torch
import torch.distributed as dist
from torch.nn.utils import clip_grad_norm_
from torch.utils.data import DataLoader, Dataset
import yaml

from model import ChatWeaverModel, ChatWeaverConfig, build_model

try:
    import sentencepiece as spm
except ImportError as exc:  # pragma: no cover - runtime check
    raise ImportError("sentencepiece is required for training") from exc


@dataclass
class OptimizerConfig:
    lr: float = 2e-4
    weight_decay: float = 0.1
    betas: Tuple[float, float] = (0.9, 0.95)
    eps: float = 1e-8
    max_grad_norm: float = 1.0


@dataclass
class SchedulerConfig:
    warmup_steps: int = 1000
    total_steps: int = 500_000
    min_lr_ratio: float = 0.1


@dataclass
class TrainingConfig:
    train_data: Sequence[str]
    eval_data: Optional[Sequence[str]] = None
    tokenizer_path: str = "tokenizer/chatweaver-spm.model"
    output_dir: str = "outputs"
    batch_size: int = 8
    micro_batch_size: int = 1
    max_steps: int = 1000
    save_interval: int = 100
    eval_interval: int = 100
    log_interval: int = 10
    precision: str = "bf16"
    gradient_accumulation: Optional[int] = None
    seed: int = 42
    fsdp: bool = False
    deepspeed_config: Optional[str] = None
    resume_from: Optional[str] = None
    lora: Optional[dict] = None

    def __post_init__(self) -> None:
        if self.gradient_accumulation is None or self.gradient_accumulation <= 0:
            self.gradient_accumulation = max(1, self.batch_size // self.micro_batch_size)


@dataclass
class LoRAConfig:
    r: int = 16
    alpha: float = 32.0
    dropout: float = 0.05
    target_modules: Tuple[str, ...] = ("q_proj", "k_proj", "v_proj", "o_proj", "w1", "w2", "w3")


class ConversationDataset(Dataset):
    """Loads Alpaca-style JSONL or plain-text corpora."""

    def __init__(
        self,
        paths: Sequence[Path],
        tokenizer: spm.SentencePieceProcessor,
        max_length: int,
    ) -> None:
        self.samples: List[List[int]] = []
        self.max_length = max_length
        for path in paths:
            if path.suffix == ".jsonl":
                self._load_jsonl(path, tokenizer)
            else:
                self._load_text(path, tokenizer)

    def _load_jsonl(self, path: Path, tokenizer: spm.SentencePieceProcessor) -> None:
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                record = json.loads(line)
                prompt = record.get("instruction", "")
                input_text = record.get("input", "")
                output_text = record.get("output", "")
                conversation = f"<|system|> {prompt}\n<|user|> {input_text}\n<|assistant|> {output_text}".strip()
                token_ids = tokenizer.encode(conversation, out_type=int)
                token_ids = token_ids[: self.max_length - 1] + [tokenizer.eos_id()]
                self.samples.append(token_ids)

    def _load_text(self, path: Path, tokenizer: spm.SentencePieceProcessor) -> None:
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                token_ids = tokenizer.encode(line, out_type=int)
                token_ids = token_ids[: self.max_length - 1] + [tokenizer.eos_id()]
                self.samples.append(token_ids)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return torch.tensor(self.samples[idx], dtype=torch.long)


def collate_batch(batch: Sequence[torch.Tensor], pad_id: int, max_length: int) -> dict:
    lengths = [min(t.size(0), max_length) for t in batch]
    padded = torch.full((len(batch), max_length), pad_id, dtype=torch.long)
    for i, seq in enumerate(batch):
        seq = seq[: max_length]
        padded[i, : seq.size(0)] = seq
    attention_mask = (padded != pad_id).long()
    labels = padded.clone()
    return {"input_ids": padded, "attention_mask": attention_mask, "labels": labels, "lengths": lengths}


def cosine_scheduler(step: int, cfg: SchedulerConfig) -> float:
    if step < cfg.warmup_steps:
        return step / max(1, cfg.warmup_steps)
    progress = (step - cfg.warmup_steps) / max(1, cfg.total_steps - cfg.warmup_steps)
    progress = min(progress, 1.0)
    cosine = 0.5 * (1 + math.cos(math.pi * progress))
    return cfg.min_lr_ratio + (1 - cfg.min_lr_ratio) * cosine


class LoRALinear(torch.nn.Module):
    """LoRA adapter for linear layers."""

    def __init__(self, base: torch.nn.Linear, r: int, alpha: float, dropout: float) -> None:
        super().__init__()
        self.base = base
        self.base.weight.requires_grad = False
        if self.base.bias is not None:
            self.base.bias.requires_grad = False
        self.r = r
        self.scaling = alpha / r
        self.dropout = torch.nn.Dropout(dropout)
        self.lora_a = torch.nn.Parameter(torch.zeros((r, base.in_features)))
        self.lora_b = torch.nn.Parameter(torch.zeros((base.out_features, r)))
        torch.nn.init.kaiming_uniform_(self.lora_a, a=math.sqrt(5))
        torch.nn.init.zeros_(self.lora_b)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        base_out = self.base(x)
        residual = self.dropout(x)
        update = (residual @ self.lora_a.t()) @ self.lora_b.t() * self.scaling
        return base_out + update


def apply_lora(model: ChatWeaverModel, cfg: LoRAConfig) -> List[torch.nn.Parameter]:
    trainable_params: List[torch.nn.Parameter] = []

    for layer in model.modules():
        for attr_name, child in list(layer.named_children()):
            if isinstance(child, torch.nn.Linear) and any(
                attr_name.endswith(target) for target in cfg.target_modules
            ):
                lora_layer = LoRALinear(child, cfg.r, cfg.alpha, cfg.dropout)
                setattr(layer, attr_name, lora_layer)
                trainable_params.extend(list(lora_layer.parameters()))
    return trainable_params


class Trainer:
    """Simple trainer supporting FSDP or standard data parallelism."""

    def __init__(
        self,
        model: ChatWeaverModel,
        optimizer: torch.optim.Optimizer,
        scheduler_cfg: SchedulerConfig,
        train_loader: DataLoader,
        eval_loader: Optional[DataLoader],
        device: torch.device,
        precision: str,
        fsdp: bool = False,
    ) -> None:
        self.model = model
        self.optimizer = optimizer
        self.scheduler_cfg = scheduler_cfg
        self.train_loader = train_loader
        self.eval_loader = eval_loader
        self.device = device
        self.precision = precision
        self.global_step = 0
        self.best_perplexity = float("inf")
        self.fsdp = fsdp

    def _autocast_dtype(self) -> torch.dtype:
        if self.precision.lower() == "bf16":
            return torch.bfloat16
        return torch.float16

    def train(
        self,
        max_steps: int,
        gradient_accumulation: int,
        save_every: int,
        eval_every: int,
        log_every: int,
        output_dir: Path,
        max_grad_norm: float,
        resume_step: int = 0,
    ) -> None:
        scaler = torch.cuda.amp.GradScaler(enabled=self.precision.lower() == "fp16")
        autocast_dtype = self._autocast_dtype()

        self.global_step = resume_step
        output_dir.mkdir(parents=True, exist_ok=True)

        for step, batch in enumerate(self.train_loader):
            self.model.train()
            batch = {k: v.to(self.device) for k, v in batch.items() if k != "lengths"}
            with torch.autocast(device_type=self.device.type, dtype=autocast_dtype):
                outputs = self.model(batch["input_ids"], attention_mask=batch["attention_mask"])
                logits = outputs["logits"][:, :-1, :]
                labels = batch["labels"][:, 1:]
                loss = torch.nn.functional.cross_entropy(
                    logits.reshape(-1, logits.size(-1)), labels.reshape(-1), ignore_index=0
                )
                loss = loss / gradient_accumulation

            if scaler.is_enabled():
                scaler.scale(loss).backward()
            else:
                loss.backward()

            if (step + 1) % gradient_accumulation == 0:
                if scaler.is_enabled():
                    scaler.unscale_(self.optimizer)
                clip_grad_norm_(self.model.parameters(), max_grad_norm)
                if scaler.is_enabled():
                    scaler.step(self.optimizer)
                    scaler.update()
                else:
                    self.optimizer.step()
                self.optimizer.zero_grad(set_to_none=True)
                self.global_step += 1

                lr_scale = cosine_scheduler(self.global_step, self.scheduler_cfg)
                for param_group in self.optimizer.param_groups:
                    param_group["lr"] = param_group["initial_lr"] * lr_scale

                if self.global_step % log_every == 0 and is_rank_zero():
                    print(f"Step {self.global_step} - loss: {loss.item() * gradient_accumulation:.4f}")

                if self.global_step % eval_every == 0 and self.eval_loader is not None:
                    metrics = self.evaluate()
                    if is_rank_zero():
                        print(f"Eval @ step {self.global_step}: {metrics}")
                    if metrics["perplexity"] < self.best_perplexity and is_rank_zero():
                        self.best_perplexity = metrics["perplexity"]
                        self._save_checkpoint(output_dir / "best.pt")

                if self.global_step % save_every == 0 and is_rank_zero():
                    self._save_checkpoint(output_dir / f"step_{self.global_step}.pt")

            if self.global_step >= max_steps:
                break

        if is_rank_zero():
            self._save_checkpoint(output_dir / "last.pt")

    def evaluate(self) -> dict:
        self.model.eval()
        perplexity_losses = []
        generated_responses = []
        references = []
        with torch.no_grad():
            for batch in self.eval_loader or []:
                lengths = batch.get("lengths", [])
                batch_tensors = {k: v.to(self.device) for k, v in batch.items() if k != "lengths"}
                outputs = self.model(
                    batch_tensors["input_ids"], attention_mask=batch_tensors["attention_mask"]
                )
                logits = outputs["logits"][:, :-1, :]
                labels = batch_tensors["labels"][:, 1:]
                loss = torch.nn.functional.cross_entropy(
                    logits.reshape(-1, logits.size(-1)), labels.reshape(-1), ignore_index=0
                )
                perplexity_losses.append(loss.item())

                for idx, length in enumerate(lengths):
                    start = max(0, length // 2)
                    generated_responses.append(
                        batch_tensors["input_ids"][idx, start:length].detach().cpu()
                    )
                    references.append(
                        batch_tensors["labels"][idx, start:length].detach().cpu()
                    )

        ppl = math.exp(sum(perplexity_losses) / max(len(perplexity_losses), 1))
        bleu = compute_bleu(generated_responses, references)
        helpfulness = compute_helpfulness(generated_responses)
        return {"perplexity": ppl, "bleu": bleu, "helpfulness": helpfulness}

    def _save_checkpoint(self, path: Path) -> None:
        checkpoint = {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "global_step": self.global_step,
        }
        torch.save(checkpoint, path)


def compute_bleu(hyps: Iterable[torch.Tensor], refs: Iterable[torch.Tensor]) -> float:
    """Compute a simple BLEU score with up to 4-grams."""

    def ngram_counts(tokens: List[int], n: int) -> dict:
        counts: dict = {}
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i : i + n])
            counts[ngram] = counts.get(ngram, 0) + 1
        return counts

    bleu_scores = []
    for hyp, ref in zip(hyps, refs):
        hyp_tokens = [tok for tok in hyp.view(-1).tolist() if tok != 0]
        ref_tokens = [tok for tok in ref.view(-1).tolist() if tok != 0]
        if not hyp_tokens or not ref_tokens:
            continue
        precisions = []
        for n in range(1, 5):
            hyp_counts = ngram_counts(hyp_tokens, n)
            ref_counts = ngram_counts(ref_tokens, n)
            overlap = sum(min(count, ref_counts.get(ng, 0)) for ng, count in hyp_counts.items())
            total = max(sum(hyp_counts.values()), 1)
            precisions.append(overlap / total)
        geo_mean = math.exp(sum(math.log(max(p, 1e-9)) for p in precisions) / 4)
        bp = math.exp(1 - len(ref_tokens) / max(len(hyp_tokens), 1)) if len(hyp_tokens) < len(ref_tokens) else 1.0
        bleu_scores.append(bp * geo_mean)
    return float(sum(bleu_scores) / max(len(bleu_scores), 1))


def compute_helpfulness(responses: Iterable[torch.Tensor]) -> float:
    """Naive helpfulness proxy based on keyword coverage."""

    helpful_keywords = {"thank", "please", "sure", "glad", "help"}
    total = 0
    helpful = 0
    for response in responses:
        text = " ".join(map(str, response.view(-1).tolist()))
        total += 1
        if any(word in text for word in helpful_keywords):
            helpful += 1
    return helpful / max(total, 1)


def is_rank_zero() -> bool:
    return not dist.is_initialized() or dist.get_rank() == 0


def setup_distributed() -> None:
    if "RANK" in os.environ and "WORLD_SIZE" in os.environ:
        dist.init_process_group(backend="nccl")
        torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))


def load_config(path: str) -> Tuple[ChatWeaverConfig, TrainingConfig, OptimizerConfig, SchedulerConfig]:
    with open(path, "r", encoding="utf-8") as fp:
        raw = yaml.safe_load(fp)

    model_cfg = ChatWeaverConfig(**raw["model"])
    train_cfg = TrainingConfig(**raw["training"])
    optim_cfg = OptimizerConfig(**raw["optimizer"])
    sched_cfg = SchedulerConfig(**raw["scheduler"])
    return model_cfg, train_cfg, optim_cfg, sched_cfg


def prepare_dataloaders(cfg: TrainingConfig, tokenizer: spm.SentencePieceProcessor, context_length: int) -> Tuple[DataLoader, Optional[DataLoader]]:
    train_paths = [Path(p) for p in cfg.train_data]
    train_dataset = ConversationDataset(train_paths, tokenizer, context_length)
    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg.micro_batch_size,
        shuffle=True,
        collate_fn=lambda batch: collate_batch(batch, tokenizer.pad_id(), context_length),
    )

    eval_loader = None
    if cfg.eval_data:
        eval_paths = [Path(p) for p in cfg.eval_data]
        eval_dataset = ConversationDataset(eval_paths, tokenizer, context_length)
        eval_loader = DataLoader(
            eval_dataset,
            batch_size=cfg.micro_batch_size,
            shuffle=False,
            collate_fn=lambda batch: collate_batch(batch, tokenizer.pad_id(), context_length),
        )
    return train_loader, eval_loader


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ChatWeaver-4B")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config file.")
    args = parser.parse_args()

    setup_distributed()
    model_cfg, train_cfg, optim_cfg, sched_cfg = load_config(args.config)

    tokenizer = spm.SentencePieceProcessor(model_file=train_cfg.tokenizer_path)

    model = build_model(model_cfg.__dict__)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    if train_cfg.lora is not None:
        for param in model.parameters():
            param.requires_grad = False
        apply_lora(model, LoRAConfig(**train_cfg.lora))

    trainable_params = [p for p in model.parameters() if p.requires_grad]

    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=optim_cfg.lr,
        betas=optim_cfg.betas,
        eps=optim_cfg.eps,
        weight_decay=optim_cfg.weight_decay,
    )
    for param_group in optimizer.param_groups:
        param_group["initial_lr"] = param_group["lr"]

    train_loader, eval_loader = prepare_dataloaders(train_cfg, tokenizer, model_cfg.context_length)

    resume_step = 0
    if train_cfg.resume_from:
        checkpoint = torch.load(train_cfg.resume_from, map_location="cpu")
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        resume_step = checkpoint.get("global_step", 0)

    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        scheduler_cfg=sched_cfg,
        train_loader=train_loader,
        eval_loader=eval_loader,
        device=device,
        precision=train_cfg.precision,
        fsdp=train_cfg.fsdp,
    )

    trainer.train(
        max_steps=train_cfg.max_steps,
        gradient_accumulation=train_cfg.gradient_accumulation,
        save_every=train_cfg.save_interval,
        eval_every=train_cfg.eval_interval,
        log_every=train_cfg.log_interval,
        output_dir=Path(train_cfg.output_dir),
        max_grad_norm=optim_cfg.max_grad_norm,
        resume_step=resume_step,
    )


if __name__ == "__main__":
    main()
