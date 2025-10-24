"""Configuration helpers for the Luau Synthesis Lab."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class LabConfig:
    allowed_sources: List[str] = field(default_factory=list)
    allowed_source_files: List[str] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)
    training: Dict[str, Any] = field(default_factory=dict)
    docs: Dict[str, Any] = field(default_factory=dict)
    _expanded_sources: List[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._expanded_sources = self._load_all_sources()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LabConfig":
        return cls(
            allowed_sources=data.get("allowed_sources", []),
            allowed_source_files=data.get("allowed_source_files", []),
            style=data.get("style", {}),
            training=data.get("training", {}),
            docs=data.get("docs", {}),
        )

    def _load_all_sources(self) -> List[str]:
        sources: List[str] = list(self.allowed_sources)
        for entry in self.allowed_source_files:
            path = Path(entry)
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                cleaned = line.strip()
                if not cleaned or cleaned.startswith("#"):
                    continue
                sources.append(cleaned)
        # Deduplicate while preserving order
        seen = set()
        unique_sources: List[str] = []
        for source in sources:
            if source not in seen:
                unique_sources.append(source)
                seen.add(source)
        return unique_sources

    def get_allowed_sources(self) -> List[str]:
        return list(self._expanded_sources)


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
                "allowed_source_files": config.allowed_source_files,
                "style": config.style,
                "training": config.training,
                "docs": config.docs,
            },
            handle,
            sort_keys=False,
        )


def export_session_history(history: List[Dict[str, str]], path: str = "session.json") -> None:
    """Persist the most recent conversation turns for inspection."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)
