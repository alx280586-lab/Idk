"""Configuration utilities for NFCE using Hydra-like patterns.

This module avoids pulling in Hydra directly for simplicity while still
supporting structured configuration with dataclasses and environment
overrides. The goal is to keep training and ingestion scripts flexible
without demanding heavy external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import os
import json


@dataclass
class LLMConfig:
    """Configuration for LLM backends used during ingestion."""

    backend: str = "claude-3-5-sonnet"
    api_base: Optional[str] = None
    api_key_env: str = "LLM_API_KEY"
    max_tokens: int = 4096
    temperature: float = 0.2


@dataclass
class StorageConfig:
    """Configuration for graph and vector storage backends."""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password_env: str = "NEO4J_PASSWORD"
    faiss_index_path: Path = Path("data/processed_graph/faiss.index")


@dataclass
class FieldConfig:
    """Configuration for semantic field simulation and models."""

    field_resolution: int = 128
    fourier_modes: int = 16
    hidden_channels: int = 64
    learning_rate: float = 1e-3
    damping: float = 0.01


@dataclass
class IngestionConfig:
    """Configuration controlling the Wikipedia ingestion pipeline."""

    dump_path: Path = Path("data/raw_wikipedia/enwiki-latest-pages-articles.xml.bz2")
    batch_size: int = 32
    commit_interval: int = 1000
    output_dir: Path = Path("data/processed_graph")
    llm: LLMConfig = field(default_factory=LLMConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)


@dataclass
class TrainingPhaseConfig:
    """Common configuration for training scripts."""

    epochs: int = 5
    log_interval: int = 10
    checkpoint_dir: Path = Path("checkpoints")
    field: FieldConfig = field(default_factory=FieldConfig)


@dataclass
class ConversationConfig:
    """Configuration for the small conversational adapter."""

    model_name: str = "phi-3-mini"
    max_new_tokens: int = 256
    style_preset: str = "concise"


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file or environment overrides.

    This helper keeps configuration minimal while enabling overrides during
    unit tests. Environment variables with prefix ``NFCE_`` are mapped into
    the resulting dictionary.
    """

    config: Dict[str, Any] = {}
    if path and path.exists():
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

    for key, value in os.environ.items():
        if key.startswith("NFCE_"):
            config[key[5:].lower()] = value
    return config


__all__ = [
    "LLMConfig",
    "StorageConfig",
    "FieldConfig",
    "IngestionConfig",
    "TrainingPhaseConfig",
    "ConversationConfig",
    "load_config",
]
