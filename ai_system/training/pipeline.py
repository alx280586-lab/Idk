"""Offline training pipeline for expanding the knowledge base."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ai_system.config import SystemConfig
from ai_system.core.memory import KnowledgeBase


class CorpusLoader:
    """Utility for loading starter scripts and conversations."""

    def __init__(self, paths: Iterable[Path]) -> None:
        self.paths = list(paths)

    def iter_scripts(self) -> Iterable[str]:
        for path in self.paths:
            for file in path.rglob("*.txt"):
                yield file.read_text()


def bootstrap_knowledge(config: SystemConfig) -> None:
    corpus = CorpusLoader(config.baseline_script_paths)
    knowledge = KnowledgeBase(config.data_root / "knowledge")
    for index, script in enumerate(corpus.iter_scripts(), start=1):
        knowledge.store(f"bootstrap_{index:04d}", script)


def export_config(config: SystemConfig, destination: Path) -> None:
    data = {
        "data_root": str(config.data_root),
        "trusted_sources": [source.__dict__ for source in config.trusted_sources],
        "baseline_script_paths": [str(path) for path in config.baseline_script_paths],
        "persona_profile": str(config.persona_profile) if config.persona_profile else None,
        "evaluation_strategies": config.evaluation_strategies,
    }
    destination.write_text(json.dumps(data, indent=2))
