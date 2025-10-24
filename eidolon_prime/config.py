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
    response_delay: float = 0.35


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

    allowed_commands: List[str] = field(
        default_factory=lambda: [
            "help",
            "status",
            "plan",
            "reflect",
            "log",
            "train",
            "atrain",
            "stop",
            "talk",
            "chat",
        ]
    )
    blocked_phrases: List[str] = field(
        default_factory=lambda: [
            "rm -rf",
            "shutdown",
            "reboot",
            "sudo ",
            "curl ",
            "wget ",
        ]
    )
    max_payload_length: int = 800


@dataclass
class WebSeed:
    """Configuration describing a trusted seed document for auto-learning."""

    url: str
    topic: str
    summary: str


@dataclass
class WebSettings:
    """Controls how the web growth system bootstraps knowledge."""

    autostart: bool = True
    cycle_batch_size: int = 50
    cycle_interval: float = 1.0
    unrestricted_access: bool = True
    trust_threshold: float = 0.6
    max_open_web_samples: int = 24
    seeds: List[WebSeed] = field(
        default_factory=lambda: [
            WebSeed(
                url="https://example.com/eidolon/primer",
                topic="primer",
                summary="Overview of Eidolon Prime's cooperative agent design.",
            ),
            WebSeed(
                url="https://example.com/eidolon/safety",
                topic="safety",
                summary="Safety checklist for verifying experiments before adoption.",
            ),
        ]
    )


@dataclass
class SyntheticSettings:
    """Controls the procedural+parametric hybrid thought engine."""

    parameter_count: int = 3_200_000
    parameter_groups: int = 16
    context_vault_size: int = 360
    max_harvest_queries: int = 4


@dataclass
class OrchestratorSettings:
    """Configures the reasoning orchestrator and trace logging."""

    trace_path: str = "trace.json"


@dataclass
class EidolonConfig:
    """Top level configuration object for the engine."""

    resources: ResourceLimits = field(default_factory=ResourceLimits)
    personality: PersonalitySettings = field(default_factory=PersonalitySettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    web: WebSettings = field(default_factory=WebSettings)
    synthetic: SyntheticSettings = field(default_factory=SyntheticSettings)
    orchestrator: OrchestratorSettings = field(default_factory=OrchestratorSettings)


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
        web=_parse_web_settings(data.get("web", {})),
        synthetic=SyntheticSettings(**data.get("synthetic", {})),
        orchestrator=OrchestratorSettings(**data.get("orchestrator", {})),
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
        "security": {
            "allowed_commands": config.security.allowed_commands,
            "blocked_phrases": config.security.blocked_phrases,
            "max_payload_length": config.security.max_payload_length,
        },
        "web": {
            "autostart": config.web.autostart,
            "cycle_batch_size": config.web.cycle_batch_size,
            "cycle_interval": config.web.cycle_interval,
            "unrestricted_access": config.web.unrestricted_access,
            "trust_threshold": config.web.trust_threshold,
            "max_open_web_samples": config.web.max_open_web_samples,
            "seeds": [vars(seed) for seed in config.web.seeds],
        },
        "synthetic": {
            "parameter_count": config.synthetic.parameter_count,
            "parameter_groups": config.synthetic.parameter_groups,
            "context_vault_size": config.synthetic.context_vault_size,
            "max_harvest_queries": config.synthetic.max_harvest_queries,
        },
        "orchestrator": {"trace_path": config.orchestrator.trace_path},
    }
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _parse_web_settings(data: dict) -> WebSettings:
    seeds_data = data.get("seeds", [])
    seeds = []
    for entry in seeds_data:
        try:
            seeds.append(WebSeed(**entry))
        except TypeError:
            # Skip malformed entries silently but continue loading others.
            continue
    defaults = WebSettings()
    settings = WebSettings(
        autostart=data.get("autostart", defaults.autostart),
        cycle_batch_size=data.get("cycle_batch_size", defaults.cycle_batch_size),
        cycle_interval=data.get("cycle_interval", defaults.cycle_interval),
        unrestricted_access=data.get("unrestricted_access", defaults.unrestricted_access),
        trust_threshold=data.get("trust_threshold", defaults.trust_threshold),
        max_open_web_samples=data.get("max_open_web_samples", defaults.max_open_web_samples),
        seeds=seeds or defaults.seeds,
    )
    return settings
