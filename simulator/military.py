"""Military module for the country simulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict
import random


@dataclass
class ForceGroup:
    size: int
    training: float
    morale: float
    equipment: float

    def combat_power(self) -> float:
        return self.size * (0.5 + self.training * 0.3 + self.morale * 0.2) * (0.5 + self.equipment * 0.5)


@dataclass
class Military:
    """Represents armed forces composition and readiness."""

    army: ForceGroup
    navy: ForceGroup
    air_force: ForceGroup
    logistics: float
    doctrine: str
    conflicts: Dict[str, str] = field(default_factory=dict)

    def total_power(self) -> float:
        return self.army.combat_power() + self.navy.combat_power() + self.air_force.combat_power()

    def update(self, funding: float, unrest: float, rng: random.Random) -> Dict[str, str]:
        events: Dict[str, str] = {}
        morale_shift = funding * 0.05 - unrest * 0.1 + rng.uniform(-0.02, 0.02)
        for force in (self.army, self.navy, self.air_force):
            force.morale = max(min(force.morale + morale_shift, 1.0), 0.1)
            force.training = max(min(force.training + funding * 0.02 - unrest * 0.02, 1.0), 0.1)
            force.equipment = max(min(force.equipment + funding * 0.03 + rng.uniform(-0.01, 0.02), 1.0), 0.1)

        self.logistics = max(min(self.logistics + funding * 0.04 + rng.uniform(-0.02, 0.02), 1.0), 0.1)

        if rng.random() < unrest * 0.05:
            events["desertion"] = "Desertions reported as unrest spreads through the ranks."

        for conflict, status in list(self.conflicts.items()):
            progress = (self.total_power() - rng.uniform(0.5, 1.5)) * 0.001
            if progress > 0:
                status = "Gaining ground"
            elif progress < 0:
                status = "Losing ground"
            else:
                status = "Stalemate"
            self.conflicts[conflict] = status

        return events

    def deploy(self, opponent_power: float, rng: random.Random) -> str:
        power_ratio = self.total_power() / max(opponent_power, 1)
        outcome_roll = rng.random() * power_ratio * self.logistics
        if outcome_roll > 1.2:
            return "Decisive victory"
        if outcome_roll > 0.9:
            return "Narrow victory"
        if outcome_roll > 0.6:
            return "Stalemate"
        if outcome_roll > 0.4:
            return "Costly defeat"
        return "Rout"

    @classmethod
    def random(cls, rng: random.Random) -> "Military":
        def group(base: int) -> ForceGroup:
            return ForceGroup(
                size=rng.randint(int(base * 0.5), int(base * 1.5)),
                training=rng.uniform(0.3, 0.8),
                morale=rng.uniform(0.3, 0.8),
                equipment=rng.uniform(0.3, 0.8),
            )

        doctrine = rng.choice([
            "Defensive",
            "Expeditionary",
            "Guerrilla",
            "Combined Arms",
            "Naval Supremacy",
        ])
        return cls(
            army=group(300_000),
            navy=group(100),
            air_force=group(1_000),
            logistics=rng.uniform(0.3, 0.8),
            doctrine=doctrine,
        )
