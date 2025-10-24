"""Stub for the web growth subsystem."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .memory import MemoryWeb
from .firewall import FirewallRing


@dataclass
class WebFinding:
    """Minimal representation of a piece of external knowledge."""

    source: str
    summary: str
    verified: bool


class WebGrowthSystem:
    """Validates and imports external findings into the Memory Web."""

    def __init__(self, memory: MemoryWeb, firewall: FirewallRing) -> None:
        self._memory = memory
        self._firewall = firewall

    def integrate(self, findings: Iterable[WebFinding]) -> int:
        imported = 0
        for finding in findings:
            if not finding.verified:
                continue
            self._memory.record("web", f"{finding.source}: {finding.summary}", 0.6, "web")
            imported += 1
        return imported

    def describe_policy(self) -> str:
        allowed = ", ".join(sorted(self._firewall._allowed))
        return f"Web integration restricted to commands: {allowed}"
