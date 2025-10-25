"""Political system model for the country simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import random


GOVERNMENT_TYPES = [
    "Democracy",
    "Constitutional Monarchy",
    "Absolute Monarchy",
    "One-Party State",
    "Military Junta",
    "Technocracy",
]


@dataclass
class PoliticalSystem:
    """Represents the political state of a country."""

    government_type: str
    approval_rating: float
    stability: float
    corruption: float
    civil_rights: float
    election_cycle: int
    next_election: int
    opposition_strength: float

    def update(self, unrest: float, rng: random.Random) -> Dict[str, str]:
        events: Dict[str, str] = {}
        approval_shift = rng.uniform(-5, 5) - unrest * 10 + (self.civil_rights - 0.5) * 5
        approval_shift -= self.corruption * 10
        self.approval_rating = max(min(self.approval_rating + approval_shift, 100), 0)

        stability_shift = rng.uniform(-0.05, 0.05) - unrest * 0.5
        stability_shift -= max(self.corruption - 0.5, 0) * 0.2
        self.stability = max(min(self.stability + stability_shift, 1.0), 0)

        corruption_shift = rng.uniform(-0.01, 0.02)
        self.corruption = max(min(self.corruption + corruption_shift, 1.0), 0.01)

        civil_rights_shift = rng.uniform(-0.02, 0.02)
        self.civil_rights = max(min(self.civil_rights + civil_rights_shift, 1.0), 0.1)

        if self.next_election <= 0 and self.government_type in {"Democracy", "Constitutional Monarchy"}:
            events["election"] = self._conduct_election(rng)
        else:
            self.next_election -= 1

        if self.stability < 0.2 and rng.random() < 0.1 + unrest:
            events["unrest"] = "Civil unrest escalates into nationwide protests."
        if self.stability < 0.1 and rng.random() < self.opposition_strength:
            events["coup"] = "A coup d'etat attempt threatens the government."

        return events

    def _conduct_election(self, rng: random.Random) -> str:
        self.next_election = self.election_cycle
        opposition_chance = self.opposition_strength + (50 - self.approval_rating) / 100
        if rng.random() < opposition_chance:
            self.government_type = rng.choice(GOVERNMENT_TYPES)
            self.approval_rating = rng.uniform(45, 65)
            self.stability = rng.uniform(0.4, 0.8)
            return "Opposition wins the election, ushering a new government."
        else:
            self.approval_rating = min(self.approval_rating + rng.uniform(2, 8), 100)
            return "Incumbent government wins re-election."

    def reform(self, civil_rights_delta: float, corruption_delta: float) -> None:
        self.civil_rights = max(min(self.civil_rights + civil_rights_delta, 1.0), 0.1)
        self.corruption = max(min(self.corruption + corruption_delta, 1.0), 0.01)
        self.approval_rating = max(min(self.approval_rating + civil_rights_delta * 40, 100), 0)

    def summary(self) -> Dict[str, float]:
        return {
            "Government": self.government_type,
            "Approval": round(self.approval_rating, 1),
            "Stability": round(self.stability, 2),
            "Corruption": round(self.corruption, 2),
            "Civil Rights": round(self.civil_rights, 2),
            "Next Election": max(self.next_election, 0),
        }

    @classmethod
    def random(cls, rng: random.Random) -> "PoliticalSystem":
        government_type = rng.choice(GOVERNMENT_TYPES)
        approval_rating = rng.uniform(40, 70)
        stability = rng.uniform(0.3, 0.9)
        corruption = rng.uniform(0.1, 0.8)
        civil_rights = rng.uniform(0.2, 0.9)
        election_cycle = rng.randint(3, 6)
        next_election = rng.randint(1, election_cycle)
        opposition_strength = rng.uniform(0.2, 0.7)
        return cls(
            government_type=government_type,
            approval_rating=approval_rating,
            stability=stability,
            corruption=corruption,
            civil_rights=civil_rights,
            election_cycle=election_cycle,
            next_election=next_election,
            opposition_strength=opposition_strength,
        )
