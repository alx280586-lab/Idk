"""Safety wrapper for command execution."""
from __future__ import annotations

from typing import Iterable, Optional


class FirewallViolation(ValueError):
    """Raised when a command violates the firewall policy."""


class FirewallRing:
    """Allow-list and content filter for collaboration commands."""

    def __init__(
        self,
        allowed_commands: Iterable[str],
        blocked_phrases: Iterable[str],
        max_payload_length: int,
    ) -> None:
        self._allowed = {command.lower() for command in allowed_commands}
        self._blocked = {phrase.lower() for phrase in blocked_phrases}
        self._max_payload_length = max_payload_length

    def permits(self, command: str) -> bool:
        return command.lower() in self._allowed

    def inspect(self, command: str, payload: Optional[str]) -> None:
        """Validate that ``payload`` complies with the firewall rules."""

        if not self.permits(command):
            raise FirewallViolation(f"Command '{command}' is not permitted.")
        if not payload:
            return
        if len(payload) > self._max_payload_length:
            raise FirewallViolation(
                "Input too long for interactive safety budget."
            )
        lowered = payload.lower()
        for phrase in self._blocked:
            if phrase and phrase in lowered:
                raise FirewallViolation(
                    "Input rejected by firewall; remove sensitive instructions."
                )
