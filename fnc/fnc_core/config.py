"""Configuration dataclasses and helpers for FNC."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GeneratorConfig:
    latent_dim: int = 256
    spectral_bases: List[str] = field(default_factory=lambda: ["fourier"])
    num_lod: int = 1
    coord_embed_dim: int = 64
    modulation_dim: int = 32
    quant_policy: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeConfig:
    cache_bytes_gpu: int = 2_000_000_000
    cache_bytes_cpu: int = 8_000_000_000
    prefetch_window: int = 4
    device_budget: str = "auto"


@dataclass
class TrainingConfig:
    optimizer: str = "adamw"
    lr: float = 1e-4
    warmup_steps: int = 2000
    batch_tokens: int = 524_288
    grad_clip: float = 1.0
    precision: str = "bf16"
    ema_decay: float = 0.999
    seed: int = 1337
    aux_weight: float = 0.0


@dataclass
class DataConfig:
    dataset_path: str = ""
    tokenizer: str = "bpe"


@dataclass
class LoggingConfig:
    wandb: bool = False
    tensorboard: bool = False


@dataclass
class ModelConfig:
    d_model: int = 2048
    n_layers: int = 24
    n_heads: int = 16
    vocab_size: int = 50257
    max_seq_len: int = 2048


@dataclass
class FNCConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    generator: GeneratorConfig = field(default_factory=GeneratorConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    data: DataConfig = field(default_factory=DataConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    extras: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FNCConfig":
        """Construct a config from nested dictionaries."""
        kwargs: Dict[str, Any] = {}
        for field_name in ("model", "generator", "runtime", "training", "data", "logging"):
            section = payload.get(field_name, {})
            dataclass_type = globals()[f"{field_name.capitalize()}Config"]
            kwargs[field_name] = dataclass_type(**section)
        kwargs["extras"] = {k: v for k, v in payload.items() if k not in kwargs}
        return cls(**kwargs)

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the configuration."""
        return {
            "model": vars(self.model),
            "generator": vars(self.generator),
            "runtime": vars(self.runtime),
            "training": vars(self.training),
            "data": vars(self.data),
            "logging": vars(self.logging),
            "extras": self.extras,
        }


__all__ = [
    "GeneratorConfig",
    "RuntimeConfig",
    "TrainingConfig",
    "DataConfig",
    "LoggingConfig",
    "ModelConfig",
    "FNCConfig",
]
