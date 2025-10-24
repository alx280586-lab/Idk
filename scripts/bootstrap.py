"""Bootstrap the system with baseline knowledge."""
from __future__ import annotations

from pathlib import Path

from ai_system.config import DEFAULT_CONFIG
from ai_system.training.pipeline import bootstrap_knowledge, export_config


if __name__ == "__main__":
    runtime_root = DEFAULT_CONFIG.data_root
    runtime_root.mkdir(parents=True, exist_ok=True)
    export_config(DEFAULT_CONFIG, runtime_root / "config.json")
    bootstrap_knowledge(DEFAULT_CONFIG)
    print(f"Bootstrap complete. Runtime data available in {runtime_root}")
