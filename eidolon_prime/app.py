"""Application bootstrap for the Eidolon Prime engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterable

from .config import EidolonConfig, load_config
from .kernel import Kernel
from .cortex import Cortex
from .memory import MemoryWeb
from .forge import Forge
from .firewall import FirewallRing
from .reflection import ReflectionEngine
from .web_growth import WebGrowthSystem
from .collaboration import CollaborationLayer
from .state import PersonalityState
from .training import TrainingGround


@dataclass
class EidolonPrimeApp:
    """Convenience wrapper that wires all engine components together."""

    config: EidolonConfig
    kernel: Kernel
    collaboration: CollaborationLayer

    @classmethod
    def from_config_path(cls, path: Optional[str] = None) -> "EidolonPrimeApp":
        config = load_config(path)
        memory = MemoryWeb()
        personality = PersonalityState()
        firewall = FirewallRing(config.security.allowed_commands)
        forge = Forge(memory)
        reflection = ReflectionEngine(personality, memory)
        web_growth = WebGrowthSystem(memory, firewall)
        training = TrainingGround(memory)
        cortex = Cortex(
            personality=personality,
            forge=forge,
            memory=memory,
            reflection=reflection,
            web_growth=web_growth,
        )
        kernel = Kernel(
            config=config,
            cortex=cortex,
            personality=personality,
            memory=memory,
            forge=forge,
            firewall=firewall,
            reflection=reflection,
            training=training,
        )
        collaboration = CollaborationLayer(kernel)
        return cls(config=config, kernel=kernel, collaboration=collaboration)

    def run_interactive(self) -> None:
        """Launch the Collaboration Layer in interactive mode."""
        self.collaboration.run_cli()

    def run_scripted(self, prompts: Iterable[str]) -> None:
        """Process a series of prompts without user interaction."""
        for prompt in prompts:
            stripped = prompt.strip()
            if not stripped:
                continue
            command = stripped.split(" ", 1)[0].lower()
            if command == "train":
                payload = stripped[len(command) :].strip()
                if not payload:
                    raise ValueError("Scripted training commands must include details.")
                receipt = self.kernel.train(payload)
                self.collaboration.render_response(prompt, receipt.render())
                continue
            if command in {"talk", "chat"}:
                message = stripped[len(command) :].strip()
                if not message:
                    raise ValueError("Scripted talk commands must include a message.")
                result = self.kernel.chat(message)
                self.collaboration.render_response(prompt, result.render())
                continue
            if not self.kernel.permits_command(command):
                raise ValueError(f"Command '{command}' is not permitted in scripted mode.")
            if command == "status":
                status = self.kernel.status()
                content = (
                    "System resources:\n"
                    + "\n".join(f"- {k}: {v}" for k, v in status.resources.items())
                    + f"\nPersonality: {status.personality}\n"
                    + "Memories:\n"
                    + (
                        "  (empty)"
                        if not status.memory_stats
                        else "\n".join(f"  {topic}: {count}" for topic, count in status.memory_stats.items())
                    )
                )
                self.collaboration.render_response(prompt, content)
                continue
            response = self.kernel.process_request(prompt)
            self.collaboration.render_response(prompt, response.render())
