"""Societal indicators for the country simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import random


RELIGIONS = [
    "Secular",
    "Christian",
    "Muslim",
    "Hindu",
    "Buddhist",
    "Traditional",
]


@dataclass
class Society:
    population: int
    happiness: float
    unrest: float
    literacy: float
    healthcare: float
    inequality: float
    median_age: float
    religion: str

    def update(self, economic_growth: float, policies: Dict[str, float], rng: random.Random) -> Dict[str, str]:
        events: Dict[str, str] = {}
        happiness_shift = economic_growth * 50
        happiness_shift += policies.get("welfare", 0) * 20
        happiness_shift += policies.get("civil_rights", 0) * 30
        happiness_shift -= policies.get("austerity", 0) * 25
        happiness_shift += rng.uniform(-5, 5)
        self.happiness = max(min(self.happiness + happiness_shift, 100), 0)

        unrest_shift = -happiness_shift / 100 + policies.get("repression", 0) * 15
        unrest_shift += self.inequality * 10 - self.literacy * 5
        unrest_shift += rng.uniform(-0.05, 0.05)
        self.unrest = max(min(self.unrest + unrest_shift, 1.0), 0)

        self.population = int(self.population * (1 + rng.uniform(-0.005, 0.015)))
        self.population = max(self.population, 100_000)

        self.literacy = max(min(self.literacy + policies.get("education", 0) * 0.05 + rng.uniform(-0.01, 0.02), 1.0), 0.1)
        self.healthcare = max(min(self.healthcare + policies.get("healthcare", 0) * 0.05 + rng.uniform(-0.01, 0.02), 1.0), 0.1)
        self.inequality = max(min(self.inequality + rng.uniform(-0.02, 0.02) - policies.get("welfare", 0) * 0.05, 1.0), 0.05)

        if self.unrest > 0.7:
            events["uprising"] = "Mass demonstrations erupt across major cities."
        elif self.unrest > 0.4:
            events["protests"] = "Protests gather momentum demanding reforms."

        return events

    def summary(self) -> Dict[str, float]:
        return {
            "Population": self.population,
            "Happiness": round(self.happiness, 1),
            "Unrest": round(self.unrest, 2),
            "Literacy": round(self.literacy, 2),
            "Healthcare": round(self.healthcare, 2),
            "Inequality": round(self.inequality, 2),
            "Median Age": round(self.median_age, 1),
            "Religion": self.religion,
        }

    @classmethod
    def random(cls, rng: random.Random) -> "Society":
        population = rng.randint(2_000_000, 200_000_000)
        happiness = rng.uniform(40, 70)
        unrest = rng.uniform(0.1, 0.4)
        literacy = rng.uniform(0.4, 0.95)
        healthcare = rng.uniform(0.3, 0.9)
        inequality = rng.uniform(0.2, 0.7)
        median_age = rng.uniform(22, 45)
        religion = rng.choice(RELIGIONS)
        return cls(
            population=population,
            happiness=happiness,
            unrest=unrest,
            literacy=literacy,
            healthcare=healthcare,
            inequality=inequality,
            median_age=median_age,
            religion=religion,
        )
