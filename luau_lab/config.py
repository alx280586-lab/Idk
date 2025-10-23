"""Configuration helpers for the Luau Synthesis Lab."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml


@dataclass
class LabConfig:
    allowed_sources: List[str] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)
    training: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LabConfig":
        return cls(
            allowed_sources=data.get("allowed_sources", []),
            style=data.get("style", {}),
            training=data.get("training", {}),
        )


def load_config(path: str = "config.yaml") -> LabConfig:
    """Load configuration from YAML or fall back to defaults."""
    if not os.path.exists(path):
        return LabConfig.from_dict({})

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return LabConfig.from_dict(data)


def save_config(config: LabConfig, path: str = "config.yaml") -> None:
    """Persist the configuration to disk."""
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(
            {
                "allowed_sources": config.allowed_sources,
                "style": config.style,
                "training": config.training,
            },
            handle,
            sort_keys=False,
        )


def export_session_history(history: List[Dict[str, str]], path: str = "session.json") -> None:
    """Persist the most recent conversation turns for inspection."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)
