"""Safety wrapper for command execution."""
from __future__ import annotations

from typing import Iterable


class FirewallRing:
    """Simple allow-list firewall for collaboration commands."""

    def __init__(self, allowed_commands: Iterable[str]) -> None:
        self._allowed = {command.lower() for command in allowed_commands}

    def permits(self, command: str) -> bool:
        return command.lower() in self._allowed
