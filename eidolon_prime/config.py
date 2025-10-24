"""Configuration loading utilities for Eidolon Prime."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import List, Optional


DEFAULT_CONFIG_PATH = "config.json"


@dataclass
class ResourceLimits:
    """Runtime resource constraints enforced by the Kernel."""

    compute_budget: float = 0.5
    max_parallel_agents: int = 3
    experiment_limit: int = 5


@dataclass
class PersonalitySettings:
    """Initial weights for the personality state vectors."""

    curiosity: float = 0.5
    confidence: float = 0.5
    empathy: float = 0.5
    integrity: float = 0.8


@dataclass
class SecuritySettings:
    """Operational safety rules."""

    allowed_commands: List[str] = field(default_factory=lambda: ["help", "status", "plan", "reflect", "log"])


@dataclass
class EidolonConfig:
    """Top level configuration object for the engine."""

    resources: ResourceLimits = field(default_factory=ResourceLimits)
    personality: PersonalitySettings = field(default_factory=PersonalitySettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)


def load_config(path: Optional[str] = None) -> EidolonConfig:
    """Load configuration from ``path`` if present, otherwise return defaults."""
    if path is None:
        path = DEFAULT_CONFIG_PATH
    file_path = Path(path)
    if not file_path.exists():
        return EidolonConfig()
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return EidolonConfig(
        resources=ResourceLimits(**data.get("resources", {})),
        personality=PersonalitySettings(**data.get("personality", {})),
        security=SecuritySettings(**data.get("security", {})),
    )


def save_default_config(path: str = DEFAULT_CONFIG_PATH) -> None:
    """Write a default configuration file to ``path`` if it is missing."""
    file_path = Path(path)
    if file_path.exists():
        return
    config = EidolonConfig()
    payload = {
        "resources": vars(config.resources),
        "personality": vars(config.personality),
        "security": {"allowed_commands": config.security.allowed_commands},
    }
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
