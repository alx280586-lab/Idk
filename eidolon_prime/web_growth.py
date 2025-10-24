"""Stub for the web growth subsystem."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

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
        self._crawl_log: List[str] = []

    def integrate(self, findings: Iterable[WebFinding]) -> int:
        imported = 0
        for finding in findings:
            if not finding.verified:
                continue
            self._memory.record("web", f"{finding.source}: {finding.summary}", 0.6, "web")
            self._crawl_log.append(finding.source)
            imported += 1
        return imported

    def describe_policy(self) -> str:
        allowed = ", ".join(sorted(self._firewall._allowed))
        if not self._crawl_log:
            return f"Web integration restricted to commands: {allowed}"
        last_sources = ", ".join(self._crawl_log[-3:])
        return (
            f"Web integration restricted to commands: {allowed}. "
            f"Latest trusted sources: {last_sources}"
        )

    def bootstrap(self, findings: Iterable[WebFinding]) -> int:
        """Ingest a batch of pre-validated findings immediately."""

        return self.integrate(findings)
