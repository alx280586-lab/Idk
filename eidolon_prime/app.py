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
        )
        collaboration = CollaborationLayer(kernel)
        return cls(config=config, kernel=kernel, collaboration=collaboration)

    def run_interactive(self) -> None:
        """Launch the Collaboration Layer in interactive mode."""
        self.collaboration.run_cli()

    def run_scripted(self, prompts: Iterable[str]) -> None:
        """Process a series of prompts without user interaction."""
        for prompt in prompts:
            response = self.kernel.process_request(prompt)
            self.collaboration.render_response(prompt, response.render())
