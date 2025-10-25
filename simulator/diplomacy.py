"""Diplomatic model for AI-driven international relations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import random


IDEOLOGIES = [
    "Liberal",
    "Conservative",
    "Socialist",
    "Nationalist",
    "Religious",
    "Technocratic",
]


@dataclass
class DiplomacyProfile:
    ideology: str
    aggression: float
    openness: float
    espionage: float


@dataclass
class Diplomacy:
    profile: DiplomacyProfile
    relations: Dict[str, float] = field(default_factory=dict)
    alliances: List[str] = field(default_factory=list)
    embargoes: List[str] = field(default_factory=list)

    def update(self, world_tension: float, rng: random.Random) -> List[str]:
        events: List[str] = []
        for partner, score in list(self.relations.items()):
            drift = rng.uniform(-5, 5) + (0.5 - world_tension) * 2
            drift += self.profile.openness * 3 - self.profile.aggression * 4
            new_score = max(min(score + drift, 100), -100)
            if new_score < -60 and partner not in self.embargoes:
                self.embargoes.append(partner)
                events.append(f"Diplomatic breakdown with {partner}.")
            elif new_score > 60 and partner not in self.alliances:
                self.alliances.append(partner)
                events.append(f"Alliance formed with {partner}.")
            self.relations[partner] = new_score
        return events

    def adjust_relation(self, partner: str, delta: float) -> None:
        self.relations[partner] = max(min(self.relations.get(partner, 0) + delta, 100), -100)

    def summary(self) -> Dict[str, List[str]]:
        return {
            "Alliances": list(self.alliances),
            "Embargoes": list(self.embargoes),
        }

    @classmethod
    def random(cls, rng: random.Random) -> "Diplomacy":
        profile = DiplomacyProfile(
            ideology=rng.choice(IDEOLOGIES),
            aggression=rng.uniform(0.1, 0.8),
            openness=rng.uniform(0.2, 0.9),
            espionage=rng.uniform(0.1, 0.9),
        )
        return cls(profile=profile)
