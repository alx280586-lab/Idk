"""Configuration schema for the organic scripting AI system."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class TrustedSource:
    """Represents a whitelisted web resource."""

    name: str
    url: str
    crawl_frequency_hours: int = 24


@dataclass
class SystemConfig:
    """Top-level configuration options for the system."""

    data_root: Path
    trusted_sources: List[TrustedSource] = field(default_factory=list)
    baseline_script_paths: List[Path] = field(default_factory=list)
    persona_profile: Path | None = None
    evaluation_strategies: Dict[str, Dict[str, str]] = field(default_factory=dict)


DEFAULT_CONFIG = SystemConfig(
    data_root=Path("./runtime"),
    trusted_sources=[
        TrustedSource(name="PythonDocs", url="https://docs.python.org/3/"),
        TrustedSource(name="MozillaMDN", url="https://developer.mozilla.org/"),
    ],
    baseline_script_paths=[
        Path("./corpus/scripts"),
    ],
    persona_profile=Path("./corpus/persona/profile.yaml"),
    evaluation_strategies={
        "script_quality": {
            "engine": "lint",
            "command": "flake8",
        },
        "conversation": {
            "engine": "rule_based",
            "policy": "./policies/dialogue_rules.yaml",
        },
    },
)
