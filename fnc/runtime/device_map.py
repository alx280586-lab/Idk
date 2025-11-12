"""Device placement heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch


@dataclass
class DeviceMap:
    """Selects CPU or GPU placement based on configuration."""

    policy: str = "auto"

    def place(self, block_spec) -> torch.device:
        if self.policy == "cpu_favored" or not torch.cuda.is_available():
            return torch.device("cpu")
        return torch.device("cuda")

    def summary(self) -> Dict[str, str]:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return {"policy": self.policy, "preferred_device": device}


__all__ = ["DeviceMap"]
